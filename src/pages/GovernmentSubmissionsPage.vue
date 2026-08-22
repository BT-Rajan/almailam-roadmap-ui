<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
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

const STATUS_OPTIONS: SelectOption[] = [
  { label: 'All Statuses', value: 'All' },
  { label: 'Draft', value: 'Draft' },
  { label: 'Submitted', value: 'Submitted' },
  { label: 'Under Review', value: 'Under Review' },
  { label: 'Comments Received', value: 'Comments Received' },
  { label: 'Approved', value: 'Approved' },
  { label: 'Rejected', value: 'Rejected' },
  { label: 'Withdrawn', value: 'Withdrawn' },
]

const authorityOptions = computed<SelectOption[]>(() => [
  { label: 'All Authorities', value: 'All' },
  ...submissionStore.authorities.map((authority) => ({ label: authority.name, value: authority.id })),
])

const TABLE_COLUMNS: SmartTableColumn<SubmissionTableRow>[] = [
  { key: 'submissionNo', label: 'Submission No.', sortable: true, width: '150px' },
  { key: 'projectName', label: 'Project', sortable: true },
  { key: 'authorityName', label: 'Authority', sortable: true },
  { key: 'formTitle', label: 'Form' },
  { key: 'status', label: 'Status', sortable: true },
  { key: 'submittedDate', label: 'Submitted', sortable: true },
  { key: 'expectedDecisionDate', label: 'Estimated Response' },
  { key: 'decisionDate', label: 'Actual Response', align: 'right' },
]

const tableRows = computed<SubmissionTableRow[]>(() =>
  submissionStore.filteredSubmissions.map((submission) => ({
    id: submission.id,
    submissionNo: submission.submissionNo,
    projectName: submissionStore.getProjectById(submission.projectId)?.projectName ?? 'Unknown Project',
    authorityName: submissionStore.getAuthorityById(submission.authorityId)?.name ?? 'Unknown Authority',
    formTitle: submissionStore.getFormById(submission.formId)?.title ?? 'Unknown Form',
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
      title="Government Submission Workspace"
      subtitle="Track every government submission from draft through approval."
    >
      <template #actions>
        <BaseButton size="sm" :icon="Plus" @click="isCreateDialogOpen = true">New Submission</BaseButton>
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
      empty-title="No submissions found"
      empty-description="Try adjusting your search or filters."
      @row-click="openSubmission"
    >
      <template #cell-status="{ value }">
        <StatusBadge :label="value as string" :variant="getSubmissionStatusVariant(value as SubmissionStatus)" />
      </template>
      <template #cell-submittedDate="{ value }">
        {{ value ? formatDate(value as string) : 'Not submitted' }}
      </template>
      <template #cell-expectedDecisionDate="{ value }">
        {{ value ? formatDate(value as string) : 'Not set' }}
      </template>
      <template #cell-decisionDate="{ value }">
        {{ value ? formatDate(value as string) : 'Not yet received' }}
      </template>
    </SmartTable>
  </div>
</template>
