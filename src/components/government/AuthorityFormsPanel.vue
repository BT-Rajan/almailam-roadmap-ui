<script setup lang="ts">
import { Download, Eye, FileEdit, Plus, Printer, Trash2 } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import DocumentPreviewDialog from '@/components/document/DocumentPreviewDialog.vue'
import ProjectFormEntryDialog from '@/components/government/ProjectFormEntryDialog.vue'
import { documentService } from '@/services/documentService'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { useProjectFormStore } from '@/stores/projectFormStore'
import { useProjectStore } from '@/stores/projectStore'
import { useToastStore } from '@/stores/toastStore'
import type { GovernmentForm, ProjectFormEntry, ProjectFormEntryStatus } from '@/types/Government'
import type { SmartTableColumn } from '@/types/Table'
import type { SelectOption } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'
import { triggerBlobDownload } from '@/utils/fileDownload'
import { formMatchesProjectService } from '@/utils/governmentFormHelpers'

const props = defineProps<{
  projectId: string
  authorityId: string
}>()

const { t } = useI18n()
const governmentSubmissionStore = useGovernmentSubmissionStore()
const projectFormStore = useProjectFormStore()
const projectStore = useProjectStore()
const toastStore = useToastStore()

const project = computed(() => projectStore.projects.find((item) => item.id === props.projectId))

const SUBMISSION_STATUS_LABEL_KEYS: Record<string, string> = {
  Draft: 'government.submissionStatus.draft',
  Submitted: 'government.submissionStatus.submitted',
  'Under Review': 'government.submissionStatus.underReview',
  'Comments Received': 'government.submissionStatus.commentsReceived',
  Approved: 'government.submissionStatus.approved',
  Rejected: 'government.submissionStatus.rejected',
  Withdrawn: 'government.submissionStatus.withdrawn',
}

const STATUS_OPTIONS = computed<SelectOption[]>(() =>
  Object.entries(SUBMISSION_STATUS_LABEL_KEYS).map(([status, key]) => ({ label: t(key), value: status })),
)

function statusLabel(status: string): string {
  const key = SUBMISSION_STATUS_LABEL_KEYS[status]
  return key ? t(key) : status
}

// Every fillable form under this authority -- the picker below only
// offers ones this project hasn't already filed (see availableForms),
// same "a form can't be added more than once" rule the backend also
// enforces.
const authorityForms = computed(() =>
  governmentSubmissionStore.forms.filter(
    (form) => form.authorityId === props.authorityId && form.status === 'Active' && Boolean(form.template),
  ),
)

// Narrowed further to forms actually relevant to this project's service
// (Administration > Service Document Map), same rule the Overview tab's
// Required Documents card and the New Submission dialog's Form picker
// both already use -- keeps "which form applies here" answered one
// consistent way everywhere it's asked.
const scopedAuthorityForms = computed(() =>
  project.value
    ? authorityForms.value.filter((form) => formMatchesProjectService(form, project.value!.service))
    : authorityForms.value,
)

// Distinguishes "no fillable forms at all for this authority" (the
// EmptyState below) from "this authority's forms just aren't mapped to
// this project's service" -- the second is fixable from Administration
// > Service Document Map, worth saying so explicitly.
const scopeMismatchHint = computed(() =>
  authorityForms.value.length > 0 && scopedAuthorityForms.value.length === 0
    ? t('government.authorityFormsPanel.scopeMismatchHint')
    : undefined,
)

const filedEntries = computed(() => projectFormStore.entriesByAuthority(props.authorityId))

const availableForms = computed(() => {
  const filedFormIds = new Set(filedEntries.value.map((entry) => entry.formId))
  return scopedAuthorityForms.value.filter((form) => !filedFormIds.has(form.id))
})

const availableFormOptions = computed<SelectOption[]>(() =>
  availableForms.value.map((form) => ({ label: `${form.formCode} · ${form.title}`, value: form.id })),
)

const selectedNewFormId = ref('')

function formById(formId: string): GovernmentForm | undefined {
  return governmentSubmissionStore.getFormById(formId)
}

interface EntryRow {
  [key: string]: unknown
  id: string
  formTitle: string
  formCode: string
  status: ProjectFormEntryStatus
  createdAt: string
  createdBy: string
}

const TABLE_COLUMNS = computed<SmartTableColumn<EntryRow>[]>(() => [
  { key: 'formCode', label: t('government.authorityFormsPanel.columnCode'), width: '110px' },
  { key: 'formTitle', label: t('government.authorityFormsPanel.columnForm'), sortable: true },
  { key: 'status', label: t('common.status'), width: '190px' },
  { key: 'createdAt', label: t('government.authorityFormsPanel.columnFiled'), sortable: true },
  { key: 'createdBy', label: t('government.authorityFormsPanel.columnFiledBy') },
])

const tableRows = computed<EntryRow[]>(() =>
  filedEntries.value.map((entry) => ({
    id: entry.id,
    formTitle: entry.formTitle,
    formCode: entry.formCode,
    status: entry.status,
    createdAt: entry.createdAt,
    createdBy: entry.createdBy ?? t('government.authorityFormsPanel.unknownFiledBy'),
  })),
)

function entryById(entryId: string): ProjectFormEntry | undefined {
  return filedEntries.value.find((entry) => entry.id === entryId)
}

async function handleStatusChange(entryId: string, status: string): Promise<void> {
  await projectFormStore.setEntryStatus(props.projectId, entryId, status as ProjectFormEntryStatus)
  if (projectFormStore.mutationError) {
    toastStore.show('error', t('government.authorityFormsPanel.couldNotChangeStatus'), projectFormStore.mutationError)
  }
}

const isDialogOpen = ref(false)
const dialogForm = ref<GovernmentForm | undefined>(undefined)
const dialogEntry = ref<ProjectFormEntry | undefined>(undefined)

function openAddDialog(): void {
  if (!selectedNewFormId.value) return
  dialogForm.value = formById(selectedNewFormId.value)
  dialogEntry.value = undefined
  isDialogOpen.value = true
}

function openEditDialog(entry: ProjectFormEntry): void {
  dialogForm.value = formById(entry.formId)
  dialogEntry.value = entry
  isDialogOpen.value = true
}

function handleDialogClosed(open: boolean): void {
  isDialogOpen.value = open
  if (!open) selectedNewFormId.value = ''
}

// Opens the filed document inline, without leaving the project
// workspace -- this used to route to the standalone /documents/:id
// page, which dropped the user out of the project entirely.
const isPreviewOpen = ref(false)
const previewDocumentId = ref<string | undefined>(undefined)

function viewDocument(entry: ProjectFormEntry): void {
  if (!entry.documentId) return
  previewDocumentId.value = entry.documentId
  isPreviewOpen.value = true
}

async function downloadDocument(entry: ProjectFormEntry): Promise<void> {
  if (!entry.documentId) return
  try {
    const blob = await documentService.downloadDocument(entry.documentId)
    triggerBlobDownload(blob, `${entry.formTitle}.pdf`)
  } catch (error) {
    toastStore.show('error', t('common.downloadFailed'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  }
}

async function printDocument(entry: ProjectFormEntry): Promise<void> {
  if (!entry.documentId) return
  try {
    const blob = await documentService.downloadDocument(entry.documentId)
    window.open(URL.createObjectURL(blob), '_blank')
  } catch (error) {
    toastStore.show('error', t('government.authorityFormsPanel.couldNotOpenDocument'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  }
}

const deleteTarget = ref<ProjectFormEntry | undefined>(undefined)
const isDeleting = ref(false)

function requestDelete(entry: ProjectFormEntry): void {
  deleteTarget.value = entry
}

async function confirmDelete(): Promise<void> {
  if (!deleteTarget.value) return
  isDeleting.value = true
  try {
    await projectFormStore.deleteEntry(props.projectId, deleteTarget.value.id)
    if (projectFormStore.mutationError) {
      toastStore.show('error', t('government.authorityFormsPanel.couldNotRemoveForm'), projectFormStore.mutationError)
    } else {
      toastStore.show('info', t('government.authorityFormsPanel.formRemovedTitle'), t('government.authorityFormsPanel.formRemovedDescription', { title: deleteTarget.value.formTitle }))
    }
    deleteTarget.value = undefined
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <EmptyState
      v-if="authorityForms.length === 0"
      :title="t('government.authorityFormsPanel.noFillableFormsTitle')"
      :description="t('government.authorityFormsPanel.noFillableFormsDescription')"
    />

    <template v-else>
      <div class="flex flex-wrap items-end gap-2 no-print">
        <div class="min-w-[16rem] flex-1">
          <SelectBox
            v-model="selectedNewFormId"
            :label="t('government.authorityFormsPanel.addAForm')"
            :placeholder="t('government.authorityFormsPanel.selectFormToFill')"
            :options="availableFormOptions"
          />
        </div>
        <BaseButton :icon="Plus" :disabled="!selectedNewFormId" @click="openAddDialog">{{ t('government.authorityFormsPanel.addForm') }}</BaseButton>
      </div>
      <p v-if="scopeMismatchHint" class="text-xs text-text-muted">{{ scopeMismatchHint }}</p>
      <p v-else-if="availableForms.length === 0" class="text-xs text-text-muted">
        {{ t('government.authorityFormsPanel.allFormsAdded') }}
      </p>

      <SmartTable
        :columns="TABLE_COLUMNS"
        :rows="tableRows"
        row-key="id"
        :loading="projectFormStore.isLoading"
        :searchable="false"
        :empty-title="t('government.authorityFormsPanel.noFormsFiledTitle')"
        :empty-description="t('government.authorityFormsPanel.noFormsFiledDescription')"
      >
        <template #cell-status="{ row }">
          <SelectBox
            :model-value="row.status as string"
            :options="STATUS_OPTIONS"
            class="no-print"
            @update:model-value="handleStatusChange(row.id as string, $event)"
          />
          <span class="hidden print:inline">{{ statusLabel(row.status as string) }}</span>
        </template>
        <template #cell-createdAt="{ value }">
          {{ formatDate(value as string) }}
        </template>
        <template #row-actions="{ row }">
          <div class="flex items-center justify-end gap-1 no-print">
            <IconButton :icon="Eye" :label="t('common.view')" size="sm" variant="ghost" @click="entryById(row.id as string) && viewDocument(entryById(row.id as string)!)" />
            <IconButton :icon="Download" :label="t('common.download')" size="sm" variant="ghost" @click="entryById(row.id as string) && downloadDocument(entryById(row.id as string)!)" />
            <IconButton :icon="Printer" :label="t('common.print')" size="sm" variant="ghost" @click="entryById(row.id as string) && printDocument(entryById(row.id as string)!)" />
            <IconButton :icon="FileEdit" :label="t('common.edit')" size="sm" variant="ghost" @click="entryById(row.id as string) && openEditDialog(entryById(row.id as string)!)" />
            <IconButton :icon="Trash2" :label="t('government.authorityFormsPanel.remove')" size="sm" variant="danger" @click="entryById(row.id as string) && requestDelete(entryById(row.id as string)!)" />
          </div>
        </template>
      </SmartTable>
    </template>

    <ProjectFormEntryDialog
      v-model="isDialogOpen"
      :project-id="projectId"
      :form="dialogForm"
      :entry="dialogEntry"
      @update:model-value="handleDialogClosed"
    />

    <ConfirmationDialog
      :model-value="!!deleteTarget"
      :title="t('government.authorityFormsPanel.removeFiledFormTitle')"
      :message="deleteTarget ? t('government.authorityFormsPanel.removeFiledFormMessage', { title: deleteTarget.formTitle }) : ''"
      :confirm-label="t('common.remove')"
      confirm-variant="danger"
      :loading="isDeleting"
      @update:model-value="deleteTarget = undefined"
      @confirm="confirmDelete"
    />

    <DocumentPreviewDialog v-model="isPreviewOpen" :document-id="previewDocumentId" />
  </div>
</template>
