<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import DetailPanel from '@/components/common/DetailPanel.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextArea from '@/components/common/TextArea.vue'
import NewSubmissionDialog from '@/components/government/NewSubmissionDialog.vue'
import RequiredDocumentChecklist from '@/components/government/RequiredDocumentChecklist.vue'
import SubmissionApprovalStepper from '@/components/government/SubmissionApprovalStepper.vue'
import type { SubmissionCreateInput } from '@/services/governmentSubmissionService'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { useToastStore } from '@/stores/toastStore'
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
const toastStore = useToastStore()
const selectedSubmissionId = ref<string | undefined>(undefined)
const isDrawerOpen = ref(false)
const isCreateDialogOpen = ref(false)
const isCreating = ref(false)

async function handleCreateSubmission(payload: SubmissionCreateInput): Promise<void> {
  isCreating.value = true
  try {
    const submission = await submissionStore.createSubmission(payload)
    toastStore.show('success', 'Submission created', `${submission.submissionNo} was created successfully.`)
    isCreateDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to create submission', detail)
  } finally {
    isCreating.value = false
  }
}
const isWithdrawDialogOpen = ref(false)
const withdrawReason = ref('')

// A submission can be withdrawn any time before a final decision has been
// made -- once Approved or Rejected (or already Withdrawn), it's terminal.
const NON_TERMINAL_STATUSES: SubmissionStatus[] = ['Draft', 'Submitted', 'Under Review', 'Comments Received']

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

const canWithdrawSelected = computed(
  () => !!selectedSubmission.value && NON_TERMINAL_STATUSES.includes(selectedSubmission.value.status),
)

function openWithdrawDialog(): void {
  withdrawReason.value = ''
  isWithdrawDialogOpen.value = true
}

async function confirmWithdraw(): Promise<void> {
  if (!selectedSubmission.value || !withdrawReason.value.trim()) return
  const success = await submissionStore.setSubmissionStatus(
    selectedSubmission.value.id,
    'Withdrawn',
    withdrawReason.value.trim(),
  )
  if (success) {
    isWithdrawDialogOpen.value = false
    toastStore.show('success', 'Submission withdrawn', `${selectedSubmission.value.submissionNo} has been withdrawn.`)
  } else {
    toastStore.show('error', 'Unable to withdraw', submissionStore.mutationError ?? 'Please try again.')
  }
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

        <div v-if="canWithdrawSelected" class="border-t border-border-light pt-4">
          <BaseButton variant="danger" size="sm" @click="openWithdrawDialog">Withdraw Submission</BaseButton>
        </div>
      </div>
    </BaseDrawer>

    <BaseDialog v-model="isWithdrawDialogOpen" title="Withdraw Submission" size="sm">
      <div class="flex flex-col gap-4">
        <p class="text-sm text-neutral-600">
          Withdrawing {{ selectedSubmission?.submissionNo }} tells the authority this submission is no longer being
          pursued. This can't be undone from here -- a new submission would need to be created to resume.
        </p>
        <TextArea
          v-model="withdrawReason"
          label="Reason for withdrawal"
          placeholder="e.g. Project scope changed, submitting a revised application instead"
          :rows="3"
        />
        <div class="flex justify-end gap-2">
          <BaseButton variant="ghost" @click="isWithdrawDialogOpen = false">Cancel</BaseButton>
          <BaseButton
            variant="danger"
            :disabled="!withdrawReason.trim()"
            :loading="submissionStore.isMutating"
            @click="confirmWithdraw"
          >
            Withdraw
          </BaseButton>
        </div>
      </div>
    </BaseDialog>
  </div>
</template>
