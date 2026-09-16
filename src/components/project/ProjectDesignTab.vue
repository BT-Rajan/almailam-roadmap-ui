<script setup lang="ts">
import { ExternalLink, FilePlus, Pencil, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import IconButton from '@/components/common/IconButton.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import DesignDocumentDialog from '@/components/document/DesignDocumentDialog.vue'
import DocumentPreviewDialog from '@/components/document/DocumentPreviewDialog.vue'
import { useDocumentStore } from '@/stores/documentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useToastStore } from '@/stores/toastStore'
import type { ProjectDocument } from '@/types/Document'
import type { Project } from '@/types/Project'
import type { SmartTableColumn } from '@/types/Table'
import { formatDate } from '@/utils/dateFormatter'

// Design's own tab (migration 0104/#3 -- previously ProjectDocumentsTab's
// mode="design", a flag on the generic any-document manager rather than a
// first-class component of its own, unlike Government Submission's
// ProjectGovernmentTab.vue and Supervision's SupervisionStatusReportsTab.vue).
// Same table/dialogs as before, lifted out unchanged -- still just the
// project's Drawing-typed ProjectDocuments, still no per-activity linkage
// (see DesignDocumentDialog.vue -- title/date/link/file only, no activity
// picker). Per-activity close/reopen controls stay on ProjectOverviewTab's
// own stage-arrival card (projectService.closeDesignActivity/
// reopenDesignActivity) -- this tab is the documents side only, same
// division Government Submission/Supervision already have between their
// own tab and Overview's activity controls.
const props = defineProps<{
  project: Project
}>()

const documentStore = useDocumentStore()
const projectStore = useProjectStore()
const toastStore = useToastStore()
const { t } = useI18n()

const isDesignDialogOpen = ref(false)
const isDesignSaving = ref(false)
const designDialogTarget = ref<ProjectDocument | null>(null)

const isDeleteDialogOpen = ref(false)
const isDeleteSaving = ref(false)
const deleteTarget = ref<ProjectDocument | null>(null)

// Mirrors the "Client Submitted" confirmation in the New Client wizard --
// a dedicated pop-up confirming what was just added (title + link), not
// just a toast, and only for a new document (editing an existing one's
// link doesn't re-show this).
const isDocumentAddedDialogOpen = ref(false)
const addedDocumentTitle = ref('')
const addedDocumentLink = ref('')

function closeDocumentAddedDialog(): void {
  isDocumentAddedDialogOpen.value = false
}

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
      await documentStore.updateDocument(target.id, payload.title, payload.link || null, payload.date)
      if (payload.file) {
        await documentStore.attachFile(target.id, payload.file)
      }
      toastStore.show('success', t('project.documentsTab.documentUpdatedTitle'), t('project.documentsTab.documentUpdatedDescription', { title: payload.title }))
    } else {
      const created = await documentStore.uploadDocument(
        payload.file,
        props.project.id,
        payload.title,
        'Drawing',
        payload.link || undefined,
      )
      if (payload.date !== created.uploadDate) {
        await documentStore.updateDocument(created.id, payload.title, payload.link || null, payload.date)
      }
      addedDocumentTitle.value = payload.title
      addedDocumentLink.value = payload.link
      isDocumentAddedDialogOpen.value = true
    }
    // A saved design link is one of the things "Design" -> "Government
    // Submission" waits on (project_service._assert_stage_exit_criteria)
    // -- refresh the shared project store so the header badge and
    // Workflow Progress stepper reflect an auto-advance immediately.
    await projectStore.refreshProject(props.project.id)
    isDesignDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', designDialogTarget.value ? t('project.documentsTab.failedToUpdateDocument') : t('project.documentsTab.failedToAddDocumentDetail'), detail)
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
    toastStore.show('success', t('project.documentsTab.documentDeletedTitle'), t('project.documentsTab.wasRemoved', { title: deleteTarget.value.title }))
    isDeleteDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('project.documentsTab.failedToDeleteDocument'), detail)
  } finally {
    isDeleteSaving.value = false
  }
}

const designDocuments = computed(() =>
  documentStore.documentsByProject(props.project.id).filter((document) => document.type === 'Drawing'),
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

const DESIGN_TABLE_COLUMNS = computed<SmartTableColumn<DesignDocumentRow>[]>(() => [
  { key: 'title', label: t('project.documentsTab.columns.document'), sortable: true },
  { key: 'fileName', label: t('project.documentsTab.columns.fileName'), sortable: true },
  { key: 'date', label: t('project.documentsTab.columns.date'), sortable: true, width: '140px' },
  { key: 'link', label: t('project.documentsTab.columns.link'), width: '120px' },
])

const designTableRows = computed<DesignDocumentRow[]>(() =>
  designDocuments.value.map((document) => ({
    id: document.id,
    title: document.title,
    fileName: document.originalFilename ?? '',
    date: document.uploadDate,
    link: document.externalLink ?? '',
    raw: document,
  })),
)

// Opens the document inline, without leaving the project workspace.
const isPreviewOpen = ref(false)
const previewDocumentId = ref<string | undefined>(undefined)

function openDocument(documentId: string): void {
  previewDocumentId.value = documentId
  isPreviewOpen.value = true
}

function loadDesignData(): void {
  if (documentStore.documents.length === 0) documentStore.loadDocuments()
}

onMounted(loadDesignData)
watch(() => props.project.id, loadDesignData)
</script>

<template>
  <div class="flex items-center justify-end">
    <BaseButton variant="secondary" size="sm" :icon="FilePlus" class="no-print" @click="openAddDesignDialog">
      {{ t('project.documentsTab.addDocument') }}
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
    :empty-title="t('project.documentsTab.emptyTitle')"
    :empty-description="t('project.documentsTab.emptyDescription')"
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
        {{ t('project.documentsTab.open') }}
      </a>
      <span v-else class="text-text-muted">—</span>
    </template>
    <template #row-actions="{ row }">
      <div class="flex items-center justify-end gap-1" @click.stop>
        <IconButton :icon="Pencil" :label="t('project.documentsTab.editDocument', { title: row.raw.title })" size="sm" variant="ghost" @click="openEditDesignDialog(row.raw)" />
        <IconButton :icon="Trash2" :label="t('project.documentsTab.deleteDocument', { title: row.raw.title })" size="sm" variant="ghost" @click="requestDelete(row.raw)" />
      </div>
    </template>
  </SmartTable>

  <DesignDocumentDialog
    v-model="isDesignDialogOpen"
    :document="designDialogTarget"
    :is-saving="isDesignSaving"
    @save="handleSaveDesignDocument"
  />
  <DocumentPreviewDialog v-model="isPreviewOpen" :document-id="previewDocumentId" />
  <ConfirmationDialog
    v-model="isDeleteDialogOpen"
    :title="t('project.documentsTab.deleteDialogTitle')"
    :message="deleteTarget ? t('project.documentsTab.deleteDialogMessage', { title: deleteTarget.title }) : ''"
    :confirm-label="t('common.delete')"
    confirm-variant="danger"
    :loading="isDeleteSaving"
    @confirm="handleConfirmDelete"
  />
  <BaseDialog :model-value="isDocumentAddedDialogOpen" :title="t('project.documentsTab.documentAddedTitle')" size="sm" :closable="false">
    <p class="text-sm text-text-secondary">
      <strong>{{ addedDocumentTitle }}</strong> {{ t('project.documentsTab.documentAddedMessage') }}
    </p>
    <p class="mt-1 truncate text-sm">
      <a :href="addedDocumentLink" target="_blank" rel="noopener noreferrer" class="text-primary-600 hover:underline">
        {{ addedDocumentLink }}
      </a>
    </p>

    <template #footer>
      <BaseButton variant="primary" @click="closeDocumentAddedDialog">{{ t('project.documentsTab.ok') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
