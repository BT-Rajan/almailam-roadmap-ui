<script setup lang="ts">
import { FilePlus } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PaginatedList from '@/components/common/PaginatedList.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import AddLinkDocumentDialog from '@/components/document/AddLinkDocumentDialog.vue'
import CustomerIdDocumentCard from '@/components/document/CustomerIdDocumentCard.vue'
import LinkDocumentCard from '@/components/document/LinkDocumentCard.vue'
import { useClientStore } from '@/stores/clientStore'
import { useProjectLinkDocumentStore } from '@/stores/projectLinkDocumentStore'
import { useToastStore } from '@/stores/toastStore'
import type { ClientDocument } from '@/types/Client'
import type { ProjectLinkDocument, ProjectLinkDocumentCategory } from '@/types/Document'
import type { Project } from '@/types/Project'

// The project's general document manager -- Customer ID / Property /
// Government / Others link-only categories. Design's own Drawing-typed
// document table used to live here too, behind a mode="design" prop
// (see ProjectDesignTab.vue, migration 0104/#3, for why that moved out).
const props = defineProps<{
  project: Project
}>()

const clientStore = useClientStore()
const linkDocumentStore = useProjectLinkDocumentStore()
const toastStore = useToastStore()
const { t } = useI18n()

const isAddDialogOpen = ref(false)
const addDialogCategory = ref<ProjectLinkDocumentCategory>('Property')
const addDialogInitialName = ref<string>()

const isLinkDeleteDialogOpen = ref(false)
const isLinkDeleteSaving = ref(false)
const linkDeleteTarget = ref<ProjectLinkDocument | null>(null)

// Customer ID Documents -- read-only, sourced from the client's own
// onboarding documents (not stored against the project at all).
const clientId = computed(() => props.project.clientId)
const customerIdDocuments = computed<ClientDocument[]>(() => clientStore.documents)

function viewCustomerDocument(document: ClientDocument): void {
  clientStore.viewDocument(clientId.value, document.id).catch(() => {
    toastStore.show('error', t('project.documentsTab.failedToOpenDocument'), t('common.pleaseTryAgain'))
  })
}

function downloadCustomerDocument(document: ClientDocument): void {
  clientStore.downloadDocument(clientId.value, document.id, document.originalFilename).catch(() => {
    toastStore.show('error', t('project.documentsTab.failedToDownloadDocument'), t('common.pleaseTryAgain'))
  })
}

// Property / Government / Others -- link-only documents added against
// the project directly.
function linkDocumentsFor(category: ProjectLinkDocumentCategory): ProjectLinkDocument[] {
  return linkDocumentStore.documentsForCategory(props.project.id, category)
}

function openAddDialog(category: ProjectLinkDocumentCategory): void {
  addDialogCategory.value = category
  addDialogInitialName.value = undefined
  isAddDialogOpen.value = true
}

function requestLinkDelete(document: ProjectLinkDocument): void {
  linkDeleteTarget.value = document
  isLinkDeleteDialogOpen.value = true
}

async function handleConfirmLinkDelete(): Promise<void> {
  if (!linkDeleteTarget.value) return
  isLinkDeleteSaving.value = true
  try {
    await linkDocumentStore.deleteDocument(props.project.id, linkDeleteTarget.value.id)
    toastStore.show('success', t('project.documentsTab.documentRemovedTitle'), t('project.documentsTab.wasRemoved', { title: linkDeleteTarget.value.name }))
    isLinkDeleteDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('project.documentsTab.failedToRemoveDocument'), detail)
  } finally {
    isLinkDeleteSaving.value = false
  }
}

function loadDocumentsData(): void {
  linkDocumentStore.loadForProject(props.project.id)
  if (clientId.value) {
    clientStore.loadClientDetail(clientId.value)
  }
}

onMounted(loadDocumentsData)
</script>

<template>
  <div class="flex flex-col gap-3">
    <!-- 1. Customer ID Documents -->
    <section class="flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-text-primary">{{ t('project.documentsTab.customerIdTitle') }}</h3>
      </div>

      <div v-if="clientStore.isDetailLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="3" />
      </div>
      <ErrorState v-else-if="clientStore.detailError" :description="clientStore.detailError" />
      <EmptyState
        v-else-if="customerIdDocuments.length === 0"
        :title="t('project.documentsTab.noIdentificationDocumentsTitle')"
        :description="t('project.documentsTab.noIdentificationDocumentsDescription')"
      />
      <PaginatedList v-else :items="customerIdDocuments" :page-size="6" :page-size-options="[6, 12, 24, 48]">
        <template #default="{ items }">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
            <CustomerIdDocumentCard
              v-for="document in items"
              :key="document.id"
              :document="document"
              @view="viewCustomerDocument"
              @download="downloadCustomerDocument"
            />
          </div>
        </template>
      </PaginatedList>
    </section>

    <!-- 2. Property Documents -->
    <section class="flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-text-primary">{{ t('project.documentsTab.propertyDocumentsTitle') }}</h3>
        <BaseButton variant="secondary" size="sm" :icon="FilePlus" class="no-print" @click="openAddDialog('Property')">
          {{ t('project.documentsTab.addDocument') }}
        </BaseButton>
      </div>

      <EmptyState
        v-if="linkDocumentsFor('Property').length === 0"
        :title="t('project.documentsTab.noPropertyDocumentsTitle')"
        :description="t('project.documentsTab.noPropertyDocumentsDescription')"
      />
      <PaginatedList v-else :items="linkDocumentsFor('Property')" :page-size="6" :page-size-options="[6, 12, 24, 48]">
        <template #default="{ items }">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
            <LinkDocumentCard
              v-for="document in items"
              :key="document.id"
              :document="document"
              @delete="requestLinkDelete"
            />
          </div>
        </template>
      </PaginatedList>
    </section>

    <!-- 3. Government Documents -->
    <section class="flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-text-primary">{{ t('project.documentsTab.governmentDocumentsTitle') }}</h3>
        <BaseButton variant="secondary" size="sm" :icon="FilePlus" class="no-print" @click="openAddDialog('Government')">
          {{ t('project.documentsTab.addDocument') }}
        </BaseButton>
      </div>

      <!-- Government forms/agreements required for this project's services
           are now handled entirely under the project's Approvals & Permits
           stage (see ProjectOverviewTab.vue's Required Documents checklist
           and ProjectGovernmentTab.vue's per-authority form filing) --
           driven by the Service Document Map (Administration), not a
           suggestion guessed here from service tags. -->
      <EmptyState
        v-if="linkDocumentsFor('Government').length === 0"
        :title="t('project.documentsTab.noGovernmentDocumentsTitle')"
        :description="t('project.documentsTab.noGovernmentDocumentsDescription')"
      />
      <PaginatedList v-else :items="linkDocumentsFor('Government')" :page-size="6" :page-size-options="[6, 12, 24, 48]">
        <template #default="{ items }">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
            <LinkDocumentCard
              v-for="document in items"
              :key="document.id"
              :document="document"
              @delete="requestLinkDelete"
            />
          </div>
        </template>
      </PaginatedList>
    </section>

    <!-- 4. Others -->
    <section class="flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-text-primary">{{ t('project.documentsTab.othersTitle') }}</h3>
        <BaseButton variant="secondary" size="sm" :icon="FilePlus" class="no-print" @click="openAddDialog('Others')">
          {{ t('project.documentsTab.addDocument') }}
        </BaseButton>
      </div>

      <EmptyState
        v-if="linkDocumentsFor('Others').length === 0"
        :title="t('project.documentsTab.noOtherDocumentsTitle')"
        :description="t('project.documentsTab.noOtherDocumentsDescription')"
      />
      <PaginatedList v-else :items="linkDocumentsFor('Others')" :page-size="6" :page-size-options="[6, 12, 24, 48]">
        <template #default="{ items }">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
            <LinkDocumentCard
              v-for="document in items"
              :key="document.id"
              :document="document"
              @delete="requestLinkDelete"
            />
          </div>
        </template>
      </PaginatedList>
    </section>

    <AddLinkDocumentDialog
      v-model="isAddDialogOpen"
      :project-id="project.id"
      :category="addDialogCategory"
      :initial-name="addDialogInitialName"
    />
    <ConfirmationDialog
      v-model="isLinkDeleteDialogOpen"
      :title="t('project.documentsTab.removeDocumentConfirmTitle')"
      :message="linkDeleteTarget ? t('project.documentsTab.removeDocumentConfirmMessage', { name: linkDeleteTarget.name }) : ''"
      :confirm-label="t('common.remove')"
      confirm-variant="danger"
      :loading="isLinkDeleteSaving"
      @confirm="handleConfirmLinkDelete"
    />
  </div>
</template>
