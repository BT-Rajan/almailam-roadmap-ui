<script setup lang="ts">
import { ChevronDown, ChevronRight, ExternalLink, FilePlus, Pencil, Trash2 } from '@lucide/vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import IconButton from '@/components/common/IconButton.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import DesignDocumentDialog from '@/components/document/DesignDocumentDialog.vue'
import DocumentPreviewDialog from '@/components/document/DocumentPreviewDialog.vue'
import { documentRequirementService } from '@/services/documentRequirementService'
import { useDocumentStore } from '@/stores/documentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useToastStore } from '@/stores/toastStore'
import type { ChecklistItem } from '@/types/DocumentRequirement'
import type { ProjectDocument } from '@/types/Document'
import type { Project } from '@/types/Project'
import type { SmartTableColumn } from '@/types/Table'
import { formatDate, formatDateTime } from '@/utils/dateFormatter'

// Design's own tab (migration 0104/#3 -- previously ProjectDocumentsTab's
// mode="design", a flag on the generic any-document manager rather than a
// first-class component of its own, unlike Government Submission's
// ProjectGovernmentTab.vue and Supervision's SupervisionStatusReportsTab.vue).
// Owns two things now: the Drawing-typed document table (unchanged from
// before) and, below it, each selected Design activity's own handover
// document checklist (#4/#5 -- checking these off is what
// project_service.assert_checklist_fulfilled actually gates on when
// closing the activity or moving the project into Handover; ticking a box
// here is no longer just for show). Per-activity close/reopen itself
// still stays on ProjectOverviewTab's own stage-arrival card
// (projectService.closeDesignActivity/reopenDesignActivity) -- this tab
// is the documents-and-checklist side only, same division Government
// Submission/Supervision already have between their own tab and
// Overview's activity controls.
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

// Handover document checklist (#4/#5) -- one disclosure per selected
// Design activity that's actually been persisted (a fresh pick in
// ServicePickerDialog has no id yet, and nothing to check a checklist
// against until the project itself is saved).
const designActivities = computed(() => (props.project.selectedActivities ?? []).filter((activity) => activity.id))

const expandedActivityIds = ref<Set<string>>(new Set())
const checklistByActivity = reactive<Record<string, ChecklistItem[]>>({})
const checklistLoadingIds = ref<Set<string>>(new Set())
const checklistErrorByActivity = reactive<Record<string, string | undefined>>({})
const savingLinkId = ref<string | null>(null)

async function loadChecklist(activityId: string): Promise<void> {
  checklistLoadingIds.value = new Set(checklistLoadingIds.value).add(activityId)
  checklistErrorByActivity[activityId] = undefined
  try {
    checklistByActivity[activityId] = await documentRequirementService.getDesignChecklist(props.project.id, activityId)
  } catch (error) {
    checklistErrorByActivity[activityId] = error instanceof Error ? error.message : t('common.pleaseTryAgain')
  } finally {
    const next = new Set(checklistLoadingIds.value)
    next.delete(activityId)
    checklistLoadingIds.value = next
  }
}

function toggleActivityChecklist(activityId: string): void {
  const next = new Set(expandedActivityIds.value)
  if (next.has(activityId)) {
    next.delete(activityId)
  } else {
    next.add(activityId)
    if (!checklistByActivity[activityId]) void loadChecklist(activityId)
  }
  expandedActivityIds.value = next
}

async function toggleChecklistItem(activityId: string, item: ChecklistItem, fulfilled: boolean): Promise<void> {
  savingLinkId.value = item.id
  try {
    checklistByActivity[activityId] = await documentRequirementService.setDesignChecklistItem(
      props.project.id, activityId, item.id, fulfilled,
    )
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain')
    toastStore.show('error', t('project.documentsTab.failedToUpdateChecklistItem'), detail)
  } finally {
    savingLinkId.value = null
  }
}
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

  <section v-if="designActivities.length > 0" class="mt-6 flex flex-col gap-3">
    <h3 class="text-sm font-semibold text-text-primary">{{ t('project.documentsTab.checklistTitle') }}</h3>
    <div
      v-for="activity in designActivities"
      :key="activity.id"
      class="rounded-xl border border-border-light bg-bg-card"
    >
      <button
        type="button"
        class="flex w-full items-center justify-between gap-2 px-4 py-3 text-left"
        @click="toggleActivityChecklist(activity.id as string)"
      >
        <span class="flex items-center gap-2 text-sm font-medium text-text-primary">
          <ChevronDown v-if="expandedActivityIds.has(activity.id as string)" class="h-4 w-4 shrink-0 text-text-muted" />
          <ChevronRight v-else class="h-4 w-4 shrink-0 text-text-muted" />
          {{ activity.activityName }}
        </span>
        <span class="text-xs text-text-muted">{{ activity.status }}</span>
      </button>

      <div v-if="expandedActivityIds.has(activity.id as string)" class="border-t border-border-light px-4 py-3">
        <SkeletonLoader v-if="checklistLoadingIds.has(activity.id as string)" :rows="2" />
        <ErrorState
          v-else-if="checklistErrorByActivity[activity.id as string]"
          :description="checklistErrorByActivity[activity.id as string]"
          @retry="loadChecklist(activity.id as string)"
        />
        <p
          v-else-if="(checklistByActivity[activity.id as string]?.length ?? 0) === 0"
          class="text-sm text-text-muted"
        >
          {{ t('project.documentsTab.checklistEmpty') }}
        </p>
        <div v-else class="flex flex-col gap-2">
          <div
            v-for="item in checklistByActivity[activity.id as string]"
            :key="item.id"
            class="flex flex-col gap-0.5"
          >
            <Checkbox
              :model-value="item.fulfilled"
              :label="item.requirementName"
              :hint="item.requirementDescription ?? undefined"
              :disabled="savingLinkId === item.id"
              @update:model-value="(value) => toggleChecklistItem(activity.id as string, item, Boolean(value))"
            />
            <p v-if="item.fulfilled && item.fulfilledByName" class="pl-7 text-xs text-text-muted">
              {{ t('project.documentsTab.checklistFulfilledBy', { name: item.fulfilledByName, date: item.fulfilledAt ? formatDateTime(item.fulfilledAt) : '' }) }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </section>

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
