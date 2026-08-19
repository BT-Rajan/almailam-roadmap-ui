<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import DetailPanel from '@/components/common/DetailPanel.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import NewSubmissionDialog from '@/components/government/NewSubmissionDialog.vue'
import RequiredDocumentChecklist from '@/components/government/RequiredDocumentChecklist.vue'
import SubmissionApprovalStepper from '@/components/government/SubmissionApprovalStepper.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import type { SubmissionCreateInput } from '@/services/governmentSubmissionService'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { useToastStore } from '@/stores/toastStore'
import { formatDate } from '@/utils/dateFormatter'
import { getSubmissionStatusVariant } from '@/utils/submissionHelpers'

const props = defineProps<{
  projectId: string
}>()

const router = useRouter()
const governmentSubmissionStore = useGovernmentSubmissionStore()
const toastStore = useToastStore()

const selectedSubmissionId = ref<string | undefined>(undefined)
const isDrawerOpen = ref(false)
const isCreateDialogOpen = ref(false)
const isCreating = ref(false)

const projectSubmissions = computed(() =>
  governmentSubmissionStore.submissionsByProject(props.projectId),
)

const selectedSubmission = computed(() =>
  projectSubmissions.value.find((submission) => submission.id === selectedSubmissionId.value),
)

const selectedSubmissionDetails = computed(() => {
  if (!selectedSubmission.value) return []
  const authority = governmentSubmissionStore.getAuthorityById(selectedSubmission.value.authorityId)
  const form = governmentSubmissionStore.getFormById(selectedSubmission.value.formId)

  return [
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

function openSubmission(submissionId: string): void {
  selectedSubmissionId.value = submissionId
  isDrawerOpen.value = true
}

async function handleCreateSubmission(payload: SubmissionCreateInput): Promise<void> {
  isCreating.value = true
  try {
    const submission = await governmentSubmissionStore.createSubmission(payload)
    toastStore.show('success', 'Submission created', `${submission.submissionNo} was created successfully.`)
    isCreateDialogOpen.value = false
  } catch (error) {
    const detail = error instanceof Error && error.message ? error.message : 'Please try again.'
    toastStore.show('error', 'Failed to create submission', detail)
  } finally {
    isCreating.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-end no-print">
    <BaseButton size="sm" :icon="Plus" @click="isCreateDialogOpen = true">New Submission</BaseButton>
  </div>

  <div v-if="governmentSubmissionStore.isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
    <SkeletonLoader :rows="6" />
  </div>

  <ErrorState
    v-else-if="governmentSubmissionStore.error"
    :description="governmentSubmissionStore.error"
    @retry="governmentSubmissionStore.loadSubmissions"
  />

  <EmptyState
    v-else-if="projectSubmissions.length === 0"
    title="No submissions yet"
    description="Government submissions filed for this project will appear here."
    action-label="New Submission"
    @action="isCreateDialogOpen = true"
  />

  <div v-else class="flex flex-col gap-3">
    <button
      v-for="submission in projectSubmissions"
      :key="submission.id"
      type="button"
      class="flex flex-col gap-2 rounded-xl border border-border-light bg-bg-card p-4 text-left shadow-soft transition-colors duration-fast hover:bg-bg-hover tablet:flex-row tablet:items-center tablet:justify-between"
      @click="openSubmission(submission.id)"
    >
      <div class="min-w-0">
        <p class="text-sm font-semibold text-neutral-800">{{ submission.submissionNo }}</p>
        <p class="truncate text-xs text-neutral-500">
          {{ governmentSubmissionStore.getFormById(submission.formId)?.title ?? 'Unknown Form' }} ·
          {{ governmentSubmissionStore.getAuthorityById(submission.authorityId)?.name ?? 'Unknown Authority' }}
        </p>
      </div>
      <StatusBadge :label="submission.status" :variant="getSubmissionStatusVariant(submission.status)" />
    </button>
  </div>

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
</template>
