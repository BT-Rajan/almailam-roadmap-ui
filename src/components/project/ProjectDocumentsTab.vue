<script setup lang="ts">
import { AlertTriangle, CheckCircle2, ExternalLink, FilePlus, Pencil, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import IconButton from '@/components/common/IconButton.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import AddLinkDocumentDialog from '@/components/document/AddLinkDocumentDialog.vue'
import CustomerIdDocumentCard from '@/components/document/CustomerIdDocumentCard.vue'
import DesignDocumentDialog from '@/components/document/DesignDocumentDialog.vue'
import LinkDocumentCard from '@/components/document/LinkDocumentCard.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useClientStore } from '@/stores/clientStore'
import { useDocumentStore } from '@/stores/documentStore'
import { useProjectLinkDocumentStore } from '@/stores/projectLinkDocumentStore'
import { useToastStore } from '@/stores/toastStore'
import type { ClientDocument } from '@/types/Client'
import type { ProjectDocument, ProjectLinkDocument, ProjectLinkDocumentCategory } from '@/types/Document'
import type { Project } from '@/types/Project'
import type { SmartTableColumn } from '@/types/Table'
import { formatDate } from '@/utils/dateFormatter'

const props = defineProps<{
  project: Project
  mode: 'documents' | 'design'
}>()

const router = useRouter()
const documentStore = useDocumentStore()
const clientStore = useClientStore()
const linkDocumentStore = useProjectLinkDocumentStore()
const toastStore = useToastStore()

const isDesignDialogOpen = ref(false)
const isDesignSaving = ref(false)
const designDialogTarget = ref<ProjectDocument | null>(null)

const isDeleteDialogOpen = ref(false)
const isDeleteSaving = ref(false)
const deleteTarget = ref<ProjectDocument | null>(null)

// Mirrors the "Client Submitted" confirmation in the New Client wizard --
// a dedicated pop-up confirming what was just added (title + link),
// not just a toast, and only for a new document (editing an existing
// one's link doesn't re-show this).
const isDocumentAddedDialogOpen = ref(false)
const addedDocumentTitle = ref('')
const addedDocumentLink = ref('')

function closeDocumentAddedDialog(): void {
  isDocumentAddedDialogOpen.value = false
}

const isAddDialogOpen = ref(false)
const addDialogCategory = ref<ProjectLinkDocumentCategory>('Property')
const addDialogInitialName = ref<string>()

const isLinkDeleteDialogOpen = ref(false)
const isLinkDeleteSaving = ref(false)
const linkDeleteTarget = ref<ProjectLinkDocument | null>(null)

function openAddDesignDialog(): void {
  designDialogTarget.value = null
  isDesignDialogOpen.value = true
}

function openEditDesignDialog(document: ProjectDocument): void {
  designDialogTarget.value = document
  isDesignDialogOpen.value = true
}

async function handleSaveDesignDocument(payload: {
  title: string
  date: string
  link: string
  file: File | undefined
}): Promise<void> {
  isDesignSaving.value = true
  try {
    if (designDialogTarget.value) {
      const target = designDialogTarget.value
      await documentStore.updateDocument(target.id, payload.title, undefined, payload.link || null, payload.date)
      if (payload.file) {
        await documentStore.attachFile(target.id, payload.file)
      }
      toastStore.show('success', 'Document updated', `${payload.title} was updated successfully.`)
    } else {
      const created = await documentStore.uploadDocument(
        payload.file,
        props.project.id,
        payload.title,
        'Drawing',
        undefined,
        payload.link || undefined,
      )
      if (payload.date !== created.uploadDate) {
        await documentStore.updateDocument(created.id, payload.title, undefined, payload.link || null, payload.date)
      }
      addedDocumentTitle.value = payload.title
      addedDocumentLink.value = payload.link
      isDocumentAddedDialogOpen.value = true
    }
    isDesignDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', designDialogTarget.value ? 'Failed to update document' : 'Failed to add document', detail)
  } finally {
    isDesignSaving.value = false
  }
}

function requestDelete(document: ProjectDocument): void {
  deleteTarget.value = document
  isDeleteDialogOpen.value = true
}

async function handleConfirmDelete(): Promise<void> {
  if (!deleteTarget.value) return
  isDeleteSaving.value = true
  try {
    await documentStore.deleteDocument(deleteTarget.value.id)
    toastStore.show('success', 'Document deleted', `${deleteTarget.value.title} was removed.`)
    isDeleteDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to delete document', detail)
  } finally {
    isDeleteSaving.value = false
  }
}

const projectDocuments = computed(() => documentStore.documentsByProject(props.project.id))
const visibleDocuments = computed(() =>
  props.mode === 'documents'
    ? projectDocuments.value
    : projectDocuments.value.filter((document) => document.type === 'Drawing'),
)

interface DesignDocumentRow {
  [key: string]: unknown
  id: string
  title: string
  fileName: string
  date: string
  link: string
  raw: ProjectDocument
}

const DESIGN_TABLE_COLUMNS: SmartTableColumn<DesignDocumentRow>[] = [
  { key: 'title', label: 'Document', sortable: true },
  { key: 'fileName', label: 'File Name', sortable: true },
  { key: 'date', label: 'Date', sortable: true, width: '140px' },
  { key: 'link', label: 'Link', width: '120px' },
]

const designTableRows = computed<DesignDocumentRow[]>(() =>
  visibleDocuments.value.map((document) => ({
    id: document.id,
    title: document.title,
    fileName: document.originalFilename ?? '',
    date: document.uploadDate,
    link: document.externalLink ?? '',
    raw: document,
  })),
)

function openDocument(documentId: string): void {
  router.push({ name: ROUTE_NAMES.DOCUMENT_VIEWER, params: { documentId } })
}

// Customer ID Documents -- read-only, sourced from the client's own
// onboarding documents (not stored against the project at all).
const clientId = computed(() => props.project.clientId)
const customerIdDocuments = computed<ClientDocument[]>(() => clientStore.documents)

function viewCustomerDocument(document: ClientDocument): void {
  clientStore.viewDocument(clientId.value, document.id).catch(() => {
    toastStore.show('error', 'Failed to open document', 'Please try again.')
  })
}

function downloadCustomerDocument(document: ClientDocument): void {
  clientStore.downloadDocument(clientId.value, document.id, document.originalFilename).catch(() => {
    toastStore.show('error', 'Failed to download document', 'Please try again.')
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

// Permits the client confirmed they already hold during project setup are
// mandatory to add here. Filed under Government Documents since that's
// where permits live; a permit counts as satisfied once some Government
// link document's name has it, loosely matched since the person adding
// it may title it "Building Permit - signed copy" etc.
const permitChecklist = computed(() =>
  (props.project.requiredPermitDocuments ?? []).map((permitName) => {
    const satisfied = linkDocumentsFor('Government').some((document) =>
      document.name.toLowerCase().includes(permitName.toLowerCase()),
    )
    return { name: permitName, satisfied }
  }),
)

function openPermitDialog(permitName: string): void {
  addDialogCategory.value = 'Government'
  addDialogInitialName.value = permitName
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
    toastStore.show('success', 'Document removed', `${linkDeleteTarget.value.name} was removed.`)
    isLinkDeleteDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to remove document', detail)
  } finally {
    isLinkDeleteSaving.value = false
  }
}

function loadDocumentsData(): void {
  if (props.mode !== 'documents') return
  linkDocumentStore.loadForProject(props.project.id)
  if (clientId.value) {
    clientStore.loadClientDetail(clientId.value)
  }
}

onMounted(loadDocumentsData)
watch(() => [props.project.id, props.mode], loadDocumentsData)
</script>

<template>
  <!-- Design mode: a single editable table of Document / File Name / Date / Link. -->
  <template v-if="mode === 'design'">
    <div class="flex items-center justify-end">
      <BaseButton variant="secondary" size="sm" :icon="FilePlus" class="no-print" @click="openAddDesignDialog">
        Add Document
      </BaseButton>
    </div>

    <ErrorState v-if="documentStore.error" :description="documentStore.error" @retry="documentStore.loadDocuments" />

    <SmartTable
      v-else
      :columns="DESIGN_TABLE_COLUMNS"
      :rows="designTableRows"
      row-key="id"
      :loading="documentStore.isLoading"
      :searchable="false"
      empty-title="No documents yet"
      empty-description="Design drawings and links added for this project will appear here."
    >
      <template #cell-fileName="{ row }">
        <button
          v-if="row.fileName"
          type="button"
          class="text-primary-600 hover:underline"
          @click.stop="openDocument(row.id)"
        >
          {{ row.fileName }}
        </button>
        <span v-else class="text-text-muted">—</span>
      </template>
      <template #cell-date="{ value }">
        {{ formatDate(value as string) }}
      </template>
      <template #cell-link="{ row }">
        <a
          v-if="row.link"
          :href="row.link as string"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center gap-1 text-primary-600 hover:underline"
          @click.stop
        >
          <ExternalLink class="h-3.5 w-3.5" />
          Open
        </a>
        <span v-else class="text-text-muted">—</span>
      </template>
      <template #row-actions="{ row }">
        <div class="flex items-center justify-end gap-1" @click.stop>
          <IconButton :icon="Pencil" label="Edit document" size="sm" variant="ghost" @click="openEditDesignDialog(row.raw)" />
          <IconButton :icon="Trash2" label="Delete document" size="sm" variant="ghost" @click="requestDelete(row.raw)" />
        </div>
      </template>
    </SmartTable>

    <DesignDocumentDialog
      v-model="isDesignDialogOpen"
      :document="designDialogTarget"
      :is-saving="isDesignSaving"
      @save="handleSaveDesignDocument"
    />
    <ConfirmationDialog
      v-model="isDeleteDialogOpen"
      title="Delete document"
      :message="deleteTarget ? `Delete ${deleteTarget.title}? This cannot be undone from the app.` : ''"
      confirm-label="Delete"
      confirm-variant="danger"
      :loading="isDeleteSaving"
      @confirm="handleConfirmDelete"
    />
    <BaseDialog :model-value="isDocumentAddedDialogOpen" title="Document Added" size="sm" :closable="false">
      <p class="text-sm text-text-secondary">
        <strong>{{ addedDocumentTitle }}</strong> was added with a link to:
      </p>
      <p class="mt-1 truncate text-sm">
        <a :href="addedDocumentLink" target="_blank" rel="noopener noreferrer" class="text-primary-600 hover:underline">
          {{ addedDocumentLink }}
        </a>
      </p>

      <template #footer>
        <BaseButton variant="primary" @click="closeDocumentAddedDialog">OK</BaseButton>
      </template>
    </BaseDialog>
  </template>

  <!-- Documents mode: four fixed categories. -->
  <div v-else class="flex flex-col gap-8">
    <!-- 0. Required Permit Documents -->
    <section v-if="permitChecklist.length > 0" class="flex flex-col gap-4">
      <h3 class="text-sm font-semibold text-text-primary">Required Permit Documents</h3>
      <div class="rounded-xl border border-border-light bg-bg-card p-4">
        <p class="mb-3 text-xs text-text-muted">
          Confirmed during project setup as permits the client already holds -- each must be added under Government
          Documents below.
        </p>
        <ul class="flex flex-col gap-2">
          <li
            v-for="permit in permitChecklist"
            :key="permit.name"
            class="flex items-center justify-between gap-3 rounded-lg border px-3 py-2 text-sm"
            :class="permit.satisfied ? 'border-success-200 bg-success-50' : 'border-warning-200 bg-warning-50'"
          >
            <span class="flex items-center gap-2">
              <CheckCircle2 v-if="permit.satisfied" class="h-4 w-4 shrink-0 text-success-600" />
              <AlertTriangle v-else class="h-4 w-4 shrink-0 text-warning-600" />
              <span :class="permit.satisfied ? 'text-text-secondary' : 'text-text-primary font-medium'">{{ permit.name }}</span>
            </span>
            <BaseButton v-if="!permit.satisfied" variant="secondary" size="sm" class="no-print" @click="openPermitDialog(permit.name)">
              Add Document
            </BaseButton>
            <span v-else class="text-xs font-medium text-success-700">Added</span>
          </li>
        </ul>
      </div>
    </section>

    <!-- 1. Customer ID Documents -->
    <section class="flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-text-primary">Customer ID Documents</h3>
      </div>

      <div v-if="clientStore.isDetailLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="3" />
      </div>
      <ErrorState v-else-if="clientStore.detailError" :description="clientStore.detailError" />
      <EmptyState
        v-else-if="customerIdDocuments.length === 0"
        title="No identification documents"
        description="Documents captured during customer onboarding will appear here."
      />
      <div v-else class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
        <CustomerIdDocumentCard
          v-for="document in customerIdDocuments"
          :key="document.id"
          :document="document"
          @view="viewCustomerDocument"
          @download="downloadCustomerDocument"
        />
      </div>
    </section>

    <!-- 2. Property Documents -->
    <section class="flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-text-primary">Property Documents</h3>
        <BaseButton variant="secondary" size="sm" :icon="FilePlus" class="no-print" @click="openAddDialog('Property')">
          Add Document
        </BaseButton>
      </div>

      <EmptyState
        v-if="linkDocumentsFor('Property').length === 0"
        title="No property documents yet"
        description="Add a link to a property document stored elsewhere."
      />
      <div v-else class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
        <LinkDocumentCard
          v-for="document in linkDocumentsFor('Property')"
          :key="document.id"
          :document="document"
          @delete="requestLinkDelete"
        />
      </div>
    </section>

    <!-- 3. Government Documents -->
    <section class="flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-text-primary">Government Documents</h3>
        <BaseButton variant="secondary" size="sm" :icon="FilePlus" class="no-print" @click="openAddDialog('Government')">
          Add Document
        </BaseButton>
      </div>

      <EmptyState
        v-if="linkDocumentsFor('Government').length === 0"
        title="No government documents yet"
        description="Add a link to a government document stored elsewhere."
      />
      <div v-else class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
        <LinkDocumentCard
          v-for="document in linkDocumentsFor('Government')"
          :key="document.id"
          :document="document"
          @delete="requestLinkDelete"
        />
      </div>
    </section>

    <!-- 4. Others -->
    <section class="flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-text-primary">Others</h3>
        <BaseButton variant="secondary" size="sm" :icon="FilePlus" class="no-print" @click="openAddDialog('Others')">
          Add Document
        </BaseButton>
      </div>

      <EmptyState
        v-if="linkDocumentsFor('Others').length === 0"
        title="No other documents yet"
        description="Add a link to any other supporting document."
      />
      <div v-else class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
        <LinkDocumentCard
          v-for="document in linkDocumentsFor('Others')"
          :key="document.id"
          :document="document"
          @delete="requestLinkDelete"
        />
      </div>
    </section>

    <AddLinkDocumentDialog
      v-model="isAddDialogOpen"
      :project-id="project.id"
      :category="addDialogCategory"
      :initial-name="addDialogInitialName"
    />
    <ConfirmationDialog
      v-model="isLinkDeleteDialogOpen"
      title="Remove document"
      :message="linkDeleteTarget ? `Remove ${linkDeleteTarget.name}? This cannot be undone from the app.` : ''"
      confirm-label="Remove"
      confirm-variant="danger"
      :loading="isLinkDeleteSaving"
      @confirm="handleConfirmLinkDelete"
    />
  </div>
</template>
