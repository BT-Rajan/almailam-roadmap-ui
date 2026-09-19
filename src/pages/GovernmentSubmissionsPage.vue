<script setup lang="ts">
import { Pencil, Plus, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import IconButton from '@/components/common/IconButton.vue'
import InlineConfirmPanel from '@/components/common/InlineConfirmPanel.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { useToastStore } from '@/stores/toastStore'
import type { SmartTableColumn } from '@/types/Table'
import type { ResponseOutcome, SubmissionStage } from '@/types/Submission'
import type { SelectOption } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'
import { getSubmissionOutcomeVariant, getSubmissionStageVariant } from '@/utils/submissionHelpers'

interface SubmissionTableRow {
  [key: string]: unknown
  id: string
  submissionNo: string
  projectName: string
  authorityName: string
  formTitle: string
  stage: SubmissionStage
  responseOutcome: ResponseOutcome | null | undefined
  submittedDate: string
  expectedDecisionDate: string
  decisionDate: string
}

const router = useRouter()
const { t } = useI18n()
const submissionStore = useGovernmentSubmissionStore()
const toastStore = useToastStore()

// Sends straight to the dedicated New Permit Application page (see
// SubmissionCreatePage.vue, which replaced NewSubmissionDialog.vue's
// modal) instead of opening a dialog here.
function goToCreateSubmission(): void {
  router.push({ name: ROUTE_NAMES.SUBMISSION_CREATE })
}

const STAGE_OPTIONS = computed<SelectOption[]>(() => [
  { label: 'All Stages', value: 'All', labelKey: 'governmentFormOptions.statusFilter.all' },
  { label: 'Prepare', value: 'Prepare', labelKey: 'government.submissionStage.prepare' },
  { label: 'Apply', value: 'Apply', labelKey: 'government.submissionStage.apply' },
  { label: 'Track', value: 'Track', labelKey: 'government.submissionStage.track' },
  { label: 'Update', value: 'Update', labelKey: 'government.submissionStage.update' },
  { label: 'Close', value: 'Close', labelKey: 'government.submissionStage.close' },
])

const authorityOptions = computed<SelectOption[]>(() => [
  { label: 'All Authorities', value: 'All', labelKey: 'government.submissionsPage.allAuthorities' },
  ...submissionStore.authorities.map((authority) => ({ label: authority.name, value: authority.id })),
])

const STAGE_LABEL_KEYS: Record<string, string> = {
  Prepare: 'government.submissionStage.prepare',
  Apply: 'government.submissionStage.apply',
  Track: 'government.submissionStage.track',
  Update: 'government.submissionStage.update',
  Close: 'government.submissionStage.close',
}

function stageLabel(stage: string): string {
  const key = STAGE_LABEL_KEYS[stage]
  return key ? t(key) : stage
}

const OUTCOME_LABEL_KEYS: Record<string, string> = {
  Approved: 'government.responseOutcome.approved',
  Rejected: 'government.responseOutcome.rejected',
  'No Response': 'government.responseOutcome.noResponse',
  Withdrawn: 'government.responseOutcome.withdrawn',
}

function outcomeLabel(outcome: string): string {
  const key = OUTCOME_LABEL_KEYS[outcome]
  return key ? t(key) : outcome
}

const TABLE_COLUMNS = computed<SmartTableColumn<SubmissionTableRow>[]>(() => [
  { key: 'submissionNo', label: t('government.submissionsPage.columnSubmissionNo'), sortable: true, width: '150px' },
  { key: 'projectName', label: t('government.submissionsPage.columnProject'), sortable: true },
  { key: 'authorityName', label: t('government.submissionsPage.columnAuthority'), sortable: true },
  { key: 'formTitle', label: t('government.submissionsPage.columnForm') },
  { key: 'stage', label: t('government.submissionsPage.columnStatus'), sortable: true },
  { key: 'submittedDate', label: t('government.submissionsPage.columnSubmitted'), sortable: true },
  { key: 'expectedDecisionDate', label: t('government.submissionsPage.columnEstimatedResponse') },
  { key: 'decisionDate', label: t('government.submissionsPage.columnActualResponse'), align: 'right' },
])

const tableRows = computed<SubmissionTableRow[]>(() =>
  submissionStore.filteredSubmissions.map((submission) => ({
    id: submission.id,
    submissionNo: submission.submissionNo,
    projectName: submissionStore.getProjectById(submission.projectId)?.projectName ?? t('government.unknownProject'),
    authorityName: submissionStore.getAuthorityById(submission.authorityId)?.name ?? t('government.unknownAuthority'),
    formTitle: submissionStore.getFormById(submission.formId)?.title ?? t('government.unknownForm'),
    stage: submission.stage,
    responseOutcome: submission.responseOutcome,
    submittedDate: submission.submittedDate ?? '',
    expectedDecisionDate: submission.expectedDecisionDate ?? '',
    decisionDate: submission.decisionDate ?? '',
  })),
)

function loadData(): void {
  submissionStore.loadSubmissions()
}

onMounted(() => {
  if (submissionStore.submissions.length === 0) loadData()
})

function openSubmission(row: SubmissionTableRow): void {
  router.push({ name: ROUTE_NAMES.SUBMISSION_WORKSPACE, params: { submissionNo: row.submissionNo } })
}

function editSubmission(row: SubmissionTableRow): void {
  router.push({ name: ROUTE_NAMES.SUBMISSION_EDIT, params: { submissionNo: row.submissionNo } })
}

// Delete asks for confirmation in a panel above the table rather than a
// modal -- see InlineConfirmPanel.vue.
const pendingDelete = ref<SubmissionTableRow>()
const isDeleting = ref(false)

const deleteConfirmMessage = computed(() => {
  const base = t('government.workspacePage.deleteConfirmMessage')
  return pendingDelete.value && pendingDelete.value.stage !== 'Prepare'
    ? `${base} ${t('government.workspacePage.deleteConfirmMessageFiled')}`
    : base
})

async function confirmDelete(): Promise<void> {
  const row = pendingDelete.value
  if (!row) return
  isDeleting.value = true
  try {
    await submissionStore.deleteSubmission(row.submissionNo)
    toastStore.show(
      'success',
      t('government.submissionsPage.submissionDeletedTitle'),
      t('government.submissionsPage.submissionDeletedDescription', { no: row.submissionNo }),
    )
  } catch (error) {
    toastStore.show('error', t('government.submissionsPage.failedToDeleteSubmission'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isDeleting.value = false
    pendingDelete.value = undefined
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader
      :title="t('government.submissionsPage.pageTitle')"
      :subtitle="t('government.submissionsPage.pageSubtitle')"
    >
      <template #actions>
        <BaseButton size="sm" :icon="Plus" @click="goToCreateSubmission">{{ t('government.submissionsPage.newSubmission') }}</BaseButton>
      </template>
    </PageHeader>

    <FilterBar
      :show-search="false"
      :has-active-filters="submissionStore.hasActiveFilters"
      @clear="submissionStore.clearFilters"
    >
      <template #filters>
        <div class="w-48">
          <SelectBox
            :model-value="submissionStore.stageFilter"
            :options="STAGE_OPTIONS"
            @update:model-value="submissionStore.setStageFilter($event as SubmissionStage | 'All')"
          />
        </div>
        <div class="w-56">
          <SelectBox
            :model-value="submissionStore.authorityFilter"
            :options="authorityOptions"
            @update:model-value="submissionStore.setAuthorityFilter($event)"
          />
        </div>
      </template>
    </FilterBar>

    <InlineConfirmPanel
      v-if="pendingDelete"
      :title="t('government.workspacePage.deleteConfirmTitle', { no: pendingDelete.submissionNo })"
      :message="deleteConfirmMessage"
      :confirm-label="t('government.workspacePage.deleteApplication')"
      :loading="isDeleting"
      @confirm="confirmDelete"
      @cancel="pendingDelete = undefined"
    />

    <ErrorState v-if="submissionStore.error" :description="submissionStore.error" @retry="loadData" />

    <SmartTable
      v-else
      :columns="TABLE_COLUMNS"
      :rows="tableRows"
      row-key="id"
      :loading="submissionStore.isLoading"
      :searchable="false"
      :empty-title="t('government.submissionsPage.noSubmissionsFound')"
      :empty-description="t('government.submissionsPage.noSubmissionsFoundDescription')"
      @row-click="openSubmission"
    >
      <template #cell-stage="{ row }">
        <StatusBadge
          v-if="row.stage === 'Close' && row.responseOutcome"
          :label="outcomeLabel(row.responseOutcome)"
          :variant="getSubmissionOutcomeVariant(row.responseOutcome)"
        />
        <StatusBadge v-else :label="stageLabel(row.stage as string)" :variant="getSubmissionStageVariant(row.stage as SubmissionStage)" />
      </template>
      <template #cell-submittedDate="{ value }">
        {{ value ? formatDate(value as string) : t('government.submissionsPage.notSubmitted') }}
      </template>
      <template #cell-expectedDecisionDate="{ value }">
        {{ value ? formatDate(value as string) : t('government.submissionsPage.notSet') }}
      </template>
      <template #cell-decisionDate="{ value }">
        {{ value ? formatDate(value as string) : t('government.submissionsPage.notYetReceived') }}
      </template>
      <template #row-actions="{ row }">
        <div class="flex items-center justify-end gap-1">
          <IconButton
            v-if="row.stage !== 'Close'"
            :icon="Pencil"
            :label="t('government.submissionsPage.editSubmission', { no: row.submissionNo })"
            size="sm"
            @click="editSubmission(row)"
          />
          <IconButton
            :icon="Trash2"
            :label="t('government.submissionsPage.deleteSubmission', { no: row.submissionNo })"
            size="sm"
            variant="danger"
            @click="pendingDelete = row"
          />
        </div>
      </template>
    </SmartTable>
  </div>
</template>
