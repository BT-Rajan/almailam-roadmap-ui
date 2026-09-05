<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import NewSubmissionDialog from '@/components/government/NewSubmissionDialog.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import type { SubmissionCreateInput } from '@/services/governmentSubmissionService'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { SmartTableColumn } from '@/types/Table'
import type { SubmissionStatus } from '@/types/Submission'
import type { SelectOption } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'
import { getSubmissionStatusVariant } from '@/utils/submissionHelpers'

interface SubmissionTableRow {
  [key: string]: unknown
  id: string
  submissionNo: string
  projectName: string
  authorityName: string
  formTitle: string
  status: SubmissionStatus
  submittedDate: string
  expectedDecisionDate: string
  decisionDate: string
}

const router = useRouter()
const { t } = useI18n()
const submissionStore = useGovernmentSubmissionStore()
const resultDialogStore = useResultDialogStore()
const isCreateDialogOpen = ref(false)
const isCreating = ref(false)

async function handleCreateSubmission(payload: SubmissionCreateInput): Promise<void> {
  isCreating.value = true
  try {
    const submission = await submissionStore.createSubmission(payload)
    resultDialogStore.showSuccess('Submission created', `${submission.submissionNo} was created successfully.`)
    isCreateDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to create submission', detail)
  } finally {
    isCreating.value = false
  }
}

const STATUS_OPTIONS = computed<SelectOption[]>(() => [
  { label: 'All Statuses', value: 'All', labelKey: 'governmentFormOptions.statusFilter.all' },
  { label: 'Draft', value: 'Draft', labelKey: 'government.submissionStatus.draft' },
  { label: 'Submitted', value: 'Submitted', labelKey: 'government.submissionStatus.submitted' },
  { label: 'Under Review', value: 'Under Review', labelKey: 'government.submissionStatus.underReview' },
  { label: 'Comments Received', value: 'Comments Received', labelKey: 'government.submissionStatus.commentsReceived' },
  { label: 'Approved', value: 'Approved', labelKey: 'government.submissionStatus.approved' },
  { label: 'Rejected', value: 'Rejected', labelKey: 'government.submissionStatus.rejected' },
  { label: 'Withdrawn', value: 'Withdrawn', labelKey: 'government.submissionStatus.withdrawn' },
])

const authorityOptions = computed<SelectOption[]>(() => [
  { label: 'All Authorities', value: 'All', labelKey: 'government.submissionsPage.allAuthorities' },
  ...submissionStore.authorities.map((authority) => ({ label: authority.name, value: authority.id })),
])

const STATUS_LABEL_KEYS: Record<string, string> = {
  Draft: 'government.submissionStatus.draft',
  Submitted: 'government.submissionStatus.submitted',
  'Under Review': 'government.submissionStatus.underReview',
  'Comments Received': 'government.submissionStatus.commentsReceived',
  Approved: 'government.submissionStatus.approved',
  Rejected: 'government.submissionStatus.rejected',
  Withdrawn: 'government.submissionStatus.withdrawn',
}

function submissionStatusLabel(status: string): string {
  const key = STATUS_LABEL_KEYS[status]
  return key ? t(key) : status
}

const TABLE_COLUMNS = computed<SmartTableColumn<SubmissionTableRow>[]>(() => [
  { key: 'submissionNo', label: t('government.submissionsPage.columnSubmissionNo'), sortable: true, width: '150px' },
  { key: 'projectName', label: t('government.submissionsPage.columnProject'), sortable: true },
  { key: 'authorityName', label: t('government.submissionsPage.columnAuthority'), sortable: true },
  { key: 'formTitle', label: t('government.submissionsPage.columnForm') },
  { key: 'status', label: t('government.submissionsPage.columnStatus'), sortable: true },
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
    status: submission.status,
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
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader
      :title="t('government.submissionsPage.pageTitle')"
      :subtitle="t('government.submissionsPage.pageSubtitle')"
    >
      <template #actions>
        <BaseButton size="sm" :icon="Plus" @click="isCreateDialogOpen = true">{{ t('government.submissionsPage.newSubmission') }}</BaseButton>
      </template>
    </PageHeader>

    <NewSubmissionDialog
      v-model="isCreateDialogOpen"
      :projects="submissionStore.projects"
      :authorities="submissionStore.authorities"
      :forms="submissionStore.forms"
      :loading="isCreating"
      @confirm="handleCreateSubmission"
    />

    <FilterBar
      :show-search="false"
      :has-active-filters="submissionStore.hasActiveFilters"
      @clear="submissionStore.clearFilters"
    >
      <template #filters>
        <div class="w-48">
          <SelectBox
            :model-value="submissionStore.statusFilter"
            :options="STATUS_OPTIONS"
            @update:model-value="submissionStore.setStatusFilter($event as SubmissionStatus | 'All')"
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
      <template #cell-status="{ value }">
        <StatusBadge :label="submissionStatusLabel(value as string)" :variant="getSubmissionStatusVariant(value as SubmissionStatus)" />
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
    </SmartTable>
  </div>
</template>
