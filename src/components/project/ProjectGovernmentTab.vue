<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import NewSubmissionDialog from '@/components/government/NewSubmissionDialog.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import type { SubmissionCreateInput } from '@/services/governmentSubmissionService'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { SmartTableColumn } from '@/types/Table'
import type { SubmissionStatus } from '@/types/Submission'
import { formatDate } from '@/utils/dateFormatter'
import { getSubmissionStatusVariant } from '@/utils/submissionHelpers'

const props = defineProps<{
  projectId: string
}>()

const router = useRouter()
const governmentSubmissionStore = useGovernmentSubmissionStore()
const resultDialogStore = useResultDialogStore()

const isCreateDialogOpen = ref(false)
const isCreating = ref(false)

const projectSubmissions = computed(() =>
  governmentSubmissionStore.submissionsByProject(props.projectId),
)

// Without this, opening this tab directly (rather than via the global
// Government Submissions Workspace page first) leaves the store's
// projects/authorities/forms empty -- New Submission's Authority and
// Form dropdowns would have nothing to select, silently blocking every
// submission from being created.
onMounted(() => {
  if (governmentSubmissionStore.submissions.length === 0) governmentSubmissionStore.loadSubmissions()
})

interface SubmissionTableRow {
  [key: string]: unknown
  id: string
  submissionNo: string
  formTitle: string
  authorityName: string
  status: SubmissionStatus
  submittedDate: string
  expectedDecisionDate: string
  decisionDate: string
}

const TABLE_COLUMNS: SmartTableColumn<SubmissionTableRow>[] = [
  { key: 'submissionNo', label: 'Submission No.', sortable: true, width: '140px' },
  { key: 'formTitle', label: 'Form', sortable: true },
  { key: 'authorityName', label: 'Authority', sortable: true },
  { key: 'submittedDate', label: 'Submitted', sortable: true },
  { key: 'expectedDecisionDate', label: 'Estimated Response' },
  { key: 'decisionDate', label: 'Actual Response' },
  { key: 'status', label: 'Status', sortable: true },
]

const tableRows = computed<SubmissionTableRow[]>(() =>
  projectSubmissions.value.map((submission) => ({
    id: submission.id,
    submissionNo: submission.submissionNo,
    formTitle: governmentSubmissionStore.getFormById(submission.formId)?.title ?? 'Unknown Form',
    authorityName: governmentSubmissionStore.getAuthorityById(submission.authorityId)?.name ?? 'Unknown Authority',
    status: submission.status,
    submittedDate: submission.submittedDate ?? '',
    expectedDecisionDate: submission.expectedDecisionDate ?? '',
    decisionDate: submission.decisionDate ?? '',
  })),
)

function openSubmission(row: SubmissionTableRow): void {
  router.push({
    name: ROUTE_NAMES.SUBMISSION_WORKSPACE,
    params: { submissionNo: row.submissionNo },
    query: { projectId: props.projectId },
  })
}

async function handleCreateSubmission(payload: SubmissionCreateInput): Promise<void> {
  isCreating.value = true
  try {
    const submission = await governmentSubmissionStore.createSubmission(payload)
    resultDialogStore.showSuccess('Submission created', `${submission.submissionNo} was created successfully.`)
    isCreateDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    resultDialogStore.showError('Failed to create submission', detail)
  } finally {
    isCreating.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-end no-print">
    <BaseButton size="sm" :icon="Plus" @click="isCreateDialogOpen = true">New Submission</BaseButton>
  </div>

  <ErrorState
    v-if="governmentSubmissionStore.error"
    :description="governmentSubmissionStore.error"
    @retry="governmentSubmissionStore.loadSubmissions"
  />

  <SmartTable
    v-else
    :columns="TABLE_COLUMNS"
    :rows="tableRows"
    row-key="id"
    :loading="governmentSubmissionStore.isLoading"
    :searchable="false"
    empty-title="No submissions yet"
    empty-description="Government submissions filed for this project will appear here."
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

  <BaseButton
    variant="ghost"
    size="sm"
    class="no-print self-start"
    @click="router.push({ name: ROUTE_NAMES.GOVERNMENT_SUBMISSIONS })"
  >
    View All Submissions
  </BaseButton>

  <NewSubmissionDialog
    v-model="isCreateDialogOpen"
    :projects="governmentSubmissionStore.projects"
    :authorities="governmentSubmissionStore.authorities"
    :forms="governmentSubmissionStore.forms"
    :default-project-id="projectId"
    :loading="isCreating"
    @confirm="handleCreateSubmission"
  />
</template>
