<script setup lang="ts">
import { FilePlus } from '@lucide/vue'
import { computed, defineAsyncComponent, onMounted, ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import AddLinkDocumentDialog from '@/components/document/AddLinkDocumentDialog.vue'
import LinkDocumentCard from '@/components/document/LinkDocumentCard.vue'
import ProjectDocumentsTab from '@/components/project/ProjectDocumentsTab.vue'
import { useProjectLinkDocumentStore } from '@/stores/projectLinkDocumentStore'
import { useToastStore } from '@/stores/toastStore'
import type { ProjectLinkDocument } from '@/types/Document'
import type { Project } from '@/types/Project'

// Lazy-loaded, same convention as ProjectWorkspacePage.vue's other
// stage-specific panels -- only fetched when this sub-tab is actually
// opened.
const ProjectGovernmentTab = defineAsyncComponent(() => import('@/components/project/ProjectGovernmentTab.vue'))

const props = defineProps<{
  project: Project
}>()

type CompletionSubTab = 'submitted' | 'approvals' | 'closure'

const SUB_TABS: { key: CompletionSubTab; label: string }[] = [
  { key: 'submitted', label: 'Submitted Docs' },
  { key: 'approvals', label: 'Approvals & Permits' },
  { key: 'closure', label: 'Project Closure Docs' },
]

const activeSubTab = ref<CompletionSubTab>('submitted')

// Project Closure Docs -- its own small CRUD section, reusing the exact
// same link-document primitives (LinkDocumentCard/AddLinkDocumentDialog)
// already used for Property/Government/Others in ProjectDocumentsTab.vue,
// just a new category rather than a new component -- completion
// certificates, handover documents, client sign-off, etc.
const linkDocumentStore = useProjectLinkDocumentStore()
const toastStore = useToastStore()

const closureDocuments = computed(() => linkDocumentStore.documentsForCategory(props.project.id, 'Project Closure'))

// Loaded here directly rather than relying on the Submitted Docs
// sub-tab's own load (ProjectDocumentsTab.vue) having run first -- this
// sub-tab needs the same store populated regardless of which one opens
// first, and Submitted Docs is unmounted (v-if) while another sub-tab
// is showing.
onMounted(() => {
  if (linkDocumentStore.documentsFor(props.project.id).length === 0) {
    linkDocumentStore.loadForProject(props.project.id)
  }
})

const isAddDialogOpen = ref(false)
const isDeleteDialogOpen = ref(false)
const isDeleteSaving = ref(false)
const deleteTarget = ref<ProjectLinkDocument | null>(null)

function requestDelete(document: ProjectLinkDocument): void {
  deleteTarget.value = document
  isDeleteDialogOpen.value = true
}

async function handleConfirmDelete(): Promise<void> {
  if (!deleteTarget.value) return
  isDeleteSaving.value = true
  try {
    await linkDocumentStore.deleteDocument(props.project.id, deleteTarget.value.id)
    toastStore.show('success', 'Document removed', `${deleteTarget.value.name} was removed.`)
    isDeleteDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to remove document', detail)
  } finally {
    isDeleteSaving.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex gap-1 overflow-x-auto border-b border-border-light no-print" role="tablist">
      <button
        v-for="tab in SUB_TABS"
        :key="tab.key"
        type="button"
        role="tab"
        class="shrink-0 whitespace-nowrap rounded-t-md border-b-2 px-4 py-3 text-sm font-medium transition-colors duration-fast focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500"
        :class="
          activeSubTab === tab.key
            ? 'border-primary-600 text-primary-700'
            : 'border-transparent text-text-muted hover:text-text-primary'
        "
        :aria-selected="activeSubTab === tab.key"
        @click="activeSubTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <ProjectDocumentsTab v-if="activeSubTab === 'submitted'" :project="project" mode="documents" />
    <ProjectGovernmentTab v-else-if="activeSubTab === 'approvals'" :project-id="project.id" />

    <div v-else class="flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-text-primary">Project Closure Documents</h3>
        <BaseButton variant="secondary" size="sm" :icon="FilePlus" class="no-print" @click="isAddDialogOpen = true">
          Add Document
        </BaseButton>
      </div>

      <EmptyState
        v-if="closureDocuments.length === 0"
        title="No closure documents yet"
        description="Add a link to a completion certificate, handover document, or other project closure record."
      />
      <div v-else class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3">
        <LinkDocumentCard
          v-for="document in closureDocuments"
          :key="document.id"
          :document="document"
          @delete="requestDelete"
        />
      </div>
    </div>

    <AddLinkDocumentDialog v-model="isAddDialogOpen" :project-id="project.id" category="Project Closure" />
    <ConfirmationDialog
      v-model="isDeleteDialogOpen"
      title="Remove document"
      :message="deleteTarget ? `Remove ${deleteTarget.name}? This cannot be undone from the app.` : ''"
      confirm-label="Remove"
      confirm-variant="danger"
      :loading="isDeleteSaving"
      @confirm="handleConfirmDelete"
    />
  </div>
</template>
