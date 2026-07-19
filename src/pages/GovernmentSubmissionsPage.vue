<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import BaseDrawer from '@/components/common/BaseDrawer.vue'
import DetailPanel from '@/components/common/DetailPanel.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import RequiredDocumentChecklist from '@/components/government/RequiredDocumentChecklist.vue'
import SubmissionApprovalStepper from '@/components/government/SubmissionApprovalStepper.vue'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
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
}

const submissionStore = useGovernmentSubmissionStore()
const selectedSubmissionId = ref<string | undefined>(undefined)
const isDrawerOpen = ref(false)

const STATUS_OPTIONS: SelectOption[] = [
  { label: 'All Statuses', value: 'All' },
  { label: 'Draft', value: 'Draft' },
  { label: 'Submitted', value: 'Submitted' },
  { label: 'Under Review', value: 'Under Review' },
  { label: 'Comments Received', value: 'Comments Received' },
  { label: 'Approved', value: 'Approved' },
  { label: 'Rejected', value: 'Rejected' },
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
  { key: 'expectedDecisionDate', label: 'Expected Decision', align: 'right' },
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
  })),
)

const selectedSubmission = computed(() =>
  submissionStore.submissions.find((submission) => submission.id === selectedSubmissionId.value),
)

const selectedSubmissionDetails = computed(() => {
  if (!selectedSubmission.value) return []
  const project = submissionStore.getProjectById(selectedSubmission.value.projectId)
  const authority = submissionStore.getAuthorityById(selectedSubmission.value.authorityId)
  const form = submissionStore.getFormById(selectedSubmission.value.formId)

  return [
    { label: 'Project', value: project?.projectName ?? 'Unknown Project' },
    { label: 'Authority', value: authority?.name ?? 'Unknown Authority' },
    { label: 'Form', value: form?.title ?? 'Unknown Form' },
    {
      label: 'Submitted Date',
      value: selectedSubmission.value.submittedDate
        ? formatDate(selectedSubmission.value.submittedDate)
        : 'Not submitted yet',
    },
    {
      label: 'Expected Decision',
      value: selectedSubmission.value.expectedDecisionDate
        ? formatDate(selectedSubmission.value.expectedDecisionDate)
        : 'Not set',
    },
  ]
})

function loadData(): void {
  submissionStore.loadSubmissions()
}

onMounted(() => {
  if (submissionStore.submissions.length === 0) loadData()
})

function openSubmission(row: SubmissionTableRow): void {
  selectedSubmissionId.value = row.id
  isDrawerOpen.value = true
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader
      title="Government Submission Workspace"
      subtitle="Track every government submission from draft through approval."
    />

    <FilterBar
      :search-value="submissionStore.searchTerm"
      search-placeholder="Search by submission number or project"
      :has-active-filters="submissionStore.hasActiveFilters"
      @update:search-value="submissionStore.setSearchTerm"
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
    </SmartTable>

    <BaseDrawer v-model="isDrawerOpen" :title="selectedSubmission?.submissionNo" width="lg">
      <div v-if="selectedSubmission" class="flex flex-col gap-6">
        <SubmissionApprovalStepper :status="selectedSubmission.status" />

        <DetailPanel title="Submission Details" :items="selectedSubmissionDetails" />

        <div>
          <h3 class="mb-2 text-sm font-semibold text-neutral-800">Required Documents</h3>
          <RequiredDocumentChecklist :documents="selectedSubmission.documents" />
        </div>

        <div v-if="selectedSubmission.notes">
          <h3 class="mb-1 text-sm font-semibold text-neutral-800">Notes</h3>
          <p class="text-sm text-neutral-600">{{ selectedSubmission.notes }}</p>
        </div>
      </div>
    </BaseDrawer>
  </div>
</template>
