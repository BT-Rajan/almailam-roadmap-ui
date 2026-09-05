<script setup lang="ts">
import { ArrowLeft, CircleCheck, Upload } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import Card from '@/components/common/Card.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import DetailPanel from '@/components/common/DetailPanel.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import TimePicker from '@/components/common/TimePicker.vue'
import RequiredDocumentChecklist from '@/components/government/RequiredDocumentChecklist.vue'
import SubmissionApprovalStepper from '@/components/government/SubmissionApprovalStepper.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { governmentSubmissionService } from '@/services/governmentSubmissionService'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { useProjectStore } from '@/stores/projectStore'
import { useToastStore } from '@/stores/toastStore'
import type { ResponseOutcome, SubmissionStatus } from '@/types/Submission'
import type { SelectOption } from '@/types/Ui'
import { triggerBlobDownload } from '@/utils/fileDownload'
import { formatDate } from '@/utils/dateFormatter'
import { getSubmissionStatusVariant } from '@/utils/submissionHelpers'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const submissionStore = useGovernmentSubmissionStore()
const projectStore = useProjectStore()
const toastStore = useToastStore()

const submissionNo = computed(() => route.params.submissionNo as string)
// Present when this page was opened with a specific project in
// context -- carried in the query rather than assumed from route
// history, so a hard refresh or a shared link still remembers where
// "back" goes.
// Without this, every route in here (Back button, breadcrumb) always
// pointed at the global Government Center submissions list, dropping
// the user out of the project they were working in.
const originProjectId = computed(() => {
  const value = route.query.projectId
  return typeof value === 'string' ? value : undefined
})
const isLoading = ref(true)
const loadError = ref<string | undefined>(undefined)

async function loadData(): Promise<void> {
  isLoading.value = true
  loadError.value = undefined
  try {
    const loaded = await submissionStore.loadSubmissionByNo(submissionNo.value)
    if (loaded && loaded.status !== 'Draft') {
      await submissionStore.loadFollowups(submissionNo.value)
    }
  } catch {
    loadError.value = 'Unable to load this submission.'
  } finally {
    isLoading.value = false
  }
}

onMounted(loadData)
watch(submissionNo, () => {
  submissionStore.followups = []
  loadData()
})

const submission = computed(() => submissionStore.getSubmissionByNo(submissionNo.value))

const project = computed(() =>
  submission.value ? submissionStore.getProjectById(submission.value.projectId) : undefined,
)
const authority = computed(() =>
  submission.value ? submissionStore.getAuthorityById(submission.value.authorityId) : undefined,
)
const form = computed(() => (submission.value ? submissionStore.getFormById(submission.value.formId) : undefined))

const submissionDetails = computed(() => {
  if (!submission.value) return []
  return [
    { label: t('government.workspacePage.detailProject'), value: project.value?.projectName ?? t('government.unknownProject') },
    { label: t('government.workspacePage.detailAuthority'), value: authority.value?.name ?? t('government.unknownAuthority') },
    { label: t('government.workspacePage.detailForm'), value: form.value?.title ?? t('government.unknownForm') },
    {
      label: t('government.workspacePage.detailSubmittedDate'),
      value: submission.value.submittedDate
        ? formatDate(submission.value.submittedDate)
        : t('government.submissionsPage.notSubmitted'),
    },
    {
      label: t('government.workspacePage.detailEstimatedResponse'),
      value: submission.value.expectedDecisionDate
        ? formatDate(submission.value.expectedDecisionDate)
        : t('government.submissionsPage.notSet'),
    },
    {
      label: t('government.workspacePage.detailActualResponse'),
      value: submission.value.decisionDate
        ? formatDate(submission.value.decisionDate)
        : t('government.submissionsPage.notYetReceived'),
    },
  ]
})

// -- Required documents ---------------------------------------------------

const canUploadDocuments = computed(() => submission.value?.status === 'Draft')
const uploadingDocumentId = ref<number>()

async function handleDocumentUpload(documentId: number, file: File): Promise<void> {
  uploadingDocumentId.value = documentId
  const success = await submissionStore.uploadDocument(submissionNo.value, documentId, file)
  uploadingDocumentId.value = undefined
  if (success) {
    toastStore.show('success', 'Document uploaded', 'The required document has been attached.')
  } else {
    toastStore.show('error', 'Upload failed', submissionStore.mutationError ?? 'Please try again.')
  }
}

async function handleDocumentDownload(documentId: number): Promise<void> {
  try {
    const blob = await governmentSubmissionService.downloadDocument(submissionNo.value, documentId)
    const doc = submission.value?.documents.find((d) => d.id === documentId)
    triggerBlobDownload(blob, doc?.originalFilename ?? 'document')
  } catch {
    toastStore.show('error', 'Download failed', 'Please try again.')
  }
}

// -- Proof of submission ---------------------------------------------------

const canUploadProofOfSubmission = computed(
  () => submission.value?.status === 'Draft' && submission.value?.allDocumentsSatisfied === true,
)
const isUploadingProofOfSubmission = ref(false)
const proofOfSubmissionInput = ref<HTMLInputElement>()

function triggerProofOfSubmissionSelect(): void {
  proofOfSubmissionInput.value?.click()
}

async function handleProofOfSubmissionUpload(event: Event): Promise<void> {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  isUploadingProofOfSubmission.value = true
  const success = await submissionStore.uploadProofOfSubmission(submissionNo.value, file)
  isUploadingProofOfSubmission.value = false
  ;(event.target as HTMLInputElement).value = ''
  if (success) {
    toastStore.show('success', 'Submission recorded', `${submissionNo.value} has been marked as Submitted.`)
  } else {
    toastStore.show('error', 'Upload failed', submissionStore.mutationError ?? 'Please try again.')
  }
}

async function downloadProofOfSubmission(): Promise<void> {
  try {
    const blob = await governmentSubmissionService.downloadProofOfSubmission(submissionNo.value)
    triggerBlobDownload(blob, submission.value?.proofOfSubmission?.originalFilename ?? 'proof-of-submission')
  } catch {
    toastStore.show('error', 'Download failed', 'Please try again.')
  }
}

// -- Follow-up log ---------------------------------------------------------

const isAwaitingResponse = computed(() =>
  ['Submitted', 'Under Review', 'Comments Received'].includes(submission.value?.status ?? ''),
)

const isFollowupDialogOpen = ref(false)
const followupDate = ref('')
const followupTime = ref('')
const followupContactPerson = ref('')
const followupNotes = ref('')

function openFollowupDialog(): void {
  followupDate.value = new Date().toISOString().slice(0, 10)
  followupTime.value = ''
  followupContactPerson.value = ''
  followupNotes.value = ''
  isFollowupDialogOpen.value = true
}

async function confirmFollowup(): Promise<void> {
  if (!followupDate.value || !followupTime.value || !followupContactPerson.value.trim()) return
  const success = await submissionStore.addFollowup(submissionNo.value, {
    followupDate: followupDate.value,
    followupTime: followupTime.value,
    contactPerson: followupContactPerson.value.trim(),
    notes: followupNotes.value.trim() || undefined,
  })
  if (success) {
    isFollowupDialogOpen.value = false
    toastStore.show('success', 'Follow-up recorded', 'The follow-up has been logged.')
  } else {
    toastStore.show('error', 'Unable to record follow-up', submissionStore.mutationError ?? 'Please try again.')
  }
}

async function loadFollowups(): Promise<void> {
  await submissionStore.loadFollowups(submissionNo.value)
}

// -- Proof of response ------------------------------------------------------

const canUploadProofOfResponse = computed(() => isAwaitingResponse.value)
const isProofOfResponseDialogOpen = ref(false)
const proofOfResponseFile = ref<File>()
const proofOfResponseOutcome = ref<ResponseOutcome>('Approved')

const OUTCOME_OPTIONS = computed<SelectOption[]>(() => [
  { label: 'Approved', value: 'Approved', labelKey: 'government.submissionStatus.approved' },
  { label: 'Rejected', value: 'Rejected', labelKey: 'government.submissionStatus.rejected' },
  { label: 'No Response', value: 'No Response', labelKey: 'government.workspacePage.outcomeNoResponse' },
])

const OUTCOME_LABEL_KEYS: Record<string, string> = {
  Approved: 'government.submissionStatus.approved',
  Rejected: 'government.submissionStatus.rejected',
  'No Response': 'government.workspacePage.outcomeNoResponse',
}

function outcomeLabel(outcome: string | null | undefined): string {
  if (!outcome) return ''
  const key = OUTCOME_LABEL_KEYS[outcome]
  return key ? t(key) : outcome
}

const SUBMISSION_STATUS_LABEL_KEYS: Record<string, string> = {
  Draft: 'government.submissionStatus.draft',
  Submitted: 'government.submissionStatus.submitted',
  'Under Review': 'government.submissionStatus.underReview',
  'Comments Received': 'government.submissionStatus.commentsReceived',
  Approved: 'government.submissionStatus.approved',
  Rejected: 'government.submissionStatus.rejected',
  Withdrawn: 'government.submissionStatus.withdrawn',
}

function submissionStatusLabel(status: string): string {
  const key = SUBMISSION_STATUS_LABEL_KEYS[status]
  return key ? t(key) : status
}

function openProofOfResponseDialog(): void {
  proofOfResponseFile.value = undefined
  proofOfResponseOutcome.value = 'Approved'
  isProofOfResponseDialogOpen.value = true
}

function handleProofOfResponseSelect(file: File | undefined): void {
  proofOfResponseFile.value = file
}

async function confirmProofOfResponse(): Promise<void> {
  if (!proofOfResponseFile.value) return
  const success = await submissionStore.uploadProofOfResponse(
    submissionNo.value,
    proofOfResponseFile.value,
    proofOfResponseOutcome.value,
  )
  if (success) {
    isProofOfResponseDialogOpen.value = false
    toastStore.show('success', 'Response recorded', "The government's response has been logged.")
  } else {
    toastStore.show('error', 'Upload failed', submissionStore.mutationError ?? 'Please try again.')
  }
}

async function downloadProofOfResponse(): Promise<void> {
  try {
    const blob = await governmentSubmissionService.downloadProofOfResponse(submissionNo.value)
    triggerBlobDownload(blob, submission.value?.proofOfResponse?.originalFilename ?? 'proof-of-response')
  } catch {
    toastStore.show('error', 'Download failed', 'Please try again.')
  }
}

// -- Mark complete -----------------------------------------------------------

const canMarkComplete = computed(
  () =>
    submission.value?.responseOutcome === 'Approved' &&
    !!submission.value?.proofOfResponse &&
    submission.value?.status !== 'Approved',
)

async function handleMarkComplete(): Promise<void> {
  const projectId = submission.value?.projectId
  const success = await submissionStore.markComplete(submissionNo.value)
  if (success) {
    toastStore.show('success', 'Submission complete', `${submissionNo.value} has been marked Approved.`)
    // A tagged submission's approval can close a project approval-process
    // gate and auto-advance the project's own stage server-side (see
    // submission_service.set_status) -- refresh so the project's cached
    // stage (used by the header/stepper if the user navigates back) isn't
    // left stale, same pattern as the other stage-advancing actions.
    if (projectId) await projectStore.refreshProject(projectId)
  } else {
    toastStore.show('error', 'Unable to mark complete', submissionStore.mutationError ?? 'Please try again.')
  }
}

function goBack(): void {
  if (originProjectId.value) {
    router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: originProjectId.value }, query: { tab: 'government' } })
    return
  }
  router.push({ name: ROUTE_NAMES.GOVERNMENT_SUBMISSIONS })
}

// -- Withdraw ----------------------------------------------------------------

const NON_TERMINAL_STATUSES: SubmissionStatus[] = ['Draft', 'Submitted', 'Under Review', 'Comments Received']
const canWithdraw = computed(
  () => !!submission.value && NON_TERMINAL_STATUSES.includes(submission.value.status),
)
const isWithdrawDialogOpen = ref(false)
const withdrawReason = ref('')

function openWithdrawDialog(): void {
  withdrawReason.value = ''
  isWithdrawDialogOpen.value = true
}

async function confirmWithdraw(): Promise<void> {
  if (!submission.value || !withdrawReason.value.trim()) return
  const success = await submissionStore.setSubmissionStatus(
    submission.value.id,
    'Withdrawn',
    withdrawReason.value.trim(),
  )
  if (success) {
    isWithdrawDialogOpen.value = false
    toastStore.show('success', 'Submission withdrawn', `${submissionNo.value} has been withdrawn.`)
  } else {
    toastStore.show('error', 'Unable to withdraw', submissionStore.mutationError ?? 'Please try again.')
  }
}

// -- Move back to Draft (e.g. after a Rejected response, to fix documents) --

const canMoveToDraft = computed(() => submission.value?.status === 'Rejected')

async function handleMoveToDraft(): Promise<void> {
  const success = await submissionStore.setSubmissionStatus(submissionNo.value, 'Draft')
  if (success) {
    toastStore.show('success', 'Moved to Draft', `${submissionNo.value} can now have its documents updated.`)
  } else {
    toastStore.show('error', 'Unable to move to Draft', submissionStore.mutationError ?? 'Please try again.')
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <BaseButton variant="ghost" size="sm" :icon="ArrowLeft" class="self-start no-print" @click="goBack">
      {{ originProjectId ? t('government.workspacePage.backToProject') : t('government.workspacePage.backToSubmissions') }}
    </BaseButton>

    <ErrorState v-if="loadError" :description="loadError" @retry="loadData" />

    <template v-else-if="isLoading">
      <div class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="4" />
      </div>
      <div class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="8" />
      </div>
    </template>

    <EmptyState
      v-else-if="!submission"
      :title="t('government.workspacePage.submissionNotFound')"
      :description="t('government.workspacePage.submissionNotFoundDescription')"
    />

    <template v-else>
      <div class="flex flex-col gap-3 tablet:flex-row tablet:items-center tablet:justify-between">
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ authority?.name ?? t('government.unknownAuthority') }} &middot; {{ form?.title ?? t('government.unknownForm') }}</p>
          <h1 class="text-xl font-semibold text-text-primary">{{ submission.submissionNo }}</h1>
        </div>
        <div class="flex items-center gap-2">
          <StatusBadge :label="submissionStatusLabel(submission.status)" :variant="getSubmissionStatusVariant(submission.status)" />
          <BaseButton v-if="canMoveToDraft" size="sm" variant="secondary" @click="handleMoveToDraft">
            {{ t('government.workspacePage.moveToDraft') }}
          </BaseButton>
          <BaseButton v-if="canWithdraw" size="sm" variant="danger" @click="openWithdrawDialog">
            {{ t('government.workspacePage.withdraw') }}
          </BaseButton>
        </div>
      </div>

      <Card>
        <SubmissionApprovalStepper :status="submission.status" />
      </Card>

      <Card>
        <template #header>
          <h3 class="text-sm font-semibold text-text-primary">{{ t('government.workspacePage.submissionDetails') }}</h3>
        </template>
        <DetailPanel :title="t('government.workspacePage.submissionDetails')" :items="submissionDetails" />
      </Card>

      <Card>
        <template #header>
          <h3 class="text-sm font-semibold text-text-primary">{{ t('government.workspacePage.requiredDocuments') }}</h3>
        </template>
        <RequiredDocumentChecklist
          :documents="submission.documents"
          :can-upload="canUploadDocuments"
          :uploading-document-id="uploadingDocumentId"
          @upload="handleDocumentUpload"
          @download="handleDocumentDownload"
        />
        <p v-if="submission.status === 'Draft' && !submission.allDocumentsSatisfied" class="mt-3 text-xs text-text-muted">
          {{ t('government.workspacePage.uploadDocumentsNotice') }}
        </p>
      </Card>

      <Card v-if="submission.status === 'Draft' || submission.proofOfSubmission">
        <template #header>
          <h3 class="text-sm font-semibold text-text-primary">{{ t('government.workspacePage.proofOfSubmission') }}</h3>
        </template>
        <div v-if="submission.proofOfSubmission" class="flex items-center justify-between gap-3">
          <span class="text-sm text-text-secondary">
            {{ submission.proofOfSubmission.originalFilename }}
            &middot; {{ submission.proofOfSubmission.fileSizeLabel }}
            &middot;
            {{
              t('government.workspacePage.uploadedByLine', {
                date: formatDate(submission.proofOfSubmission.uploadDate),
                user: submission.proofOfSubmission.uploadedBy,
              })
            }}
          </span>
          <BaseButton variant="secondary" size="sm" @click="downloadProofOfSubmission">{{ t('government.workspacePage.download') }}</BaseButton>
        </div>
        <div v-else-if="canUploadProofOfSubmission" class="flex flex-col gap-2">
          <p class="text-sm text-text-secondary">
            {{ t('government.workspacePage.allDocumentsUploadedNotice') }}
          </p>
          <BaseButton size="sm" :icon="Upload" :loading="isUploadingProofOfSubmission" @click="triggerProofOfSubmissionSelect">
            {{ t('government.workspacePage.uploadProofOfSubmission') }}
          </BaseButton>
          <input
            ref="proofOfSubmissionInput"
            type="file"
            class="hidden"
            accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.tiff,.tif"
            @change="handleProofOfSubmissionUpload"
          />
        </div>
        <p v-else class="text-sm text-text-muted">
          {{ t('government.workspacePage.uploadDocumentsBeforeProofNotice') }}
        </p>
      </Card>

      <Card v-if="isAwaitingResponse || submissionStore.followups.length > 0">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-semibold text-text-primary">{{ t('government.workspacePage.followUpLog') }}</h3>
            <BaseButton v-if="isAwaitingResponse" size="sm" variant="secondary" @click="openFollowupDialog">
              {{ t('government.workspacePage.recordFollowUp') }}
            </BaseButton>
          </div>
        </template>
        <div v-if="submissionStore.followups.length === 0" class="text-sm text-text-muted">
          {{ t('government.workspacePage.noFollowUpsRecorded') }}
        </div>
        <ul v-else class="flex flex-col divide-y divide-border-light">
          <li v-for="followup in submissionStore.followups" :key="followup.id" class="flex flex-col gap-1 py-3">
            <div class="flex items-center justify-between gap-3">
              <span class="text-sm font-medium text-text-primary">{{ followup.contactPerson }}</span>
              <span class="text-xs text-text-muted">{{
                t('government.workspacePage.followUpAt', { date: formatDate(followup.followupDate), time: followup.followupTime })
              }}</span>
            </div>
            <p v-if="followup.notes" class="text-sm text-text-secondary">{{ followup.notes }}</p>
            <p class="text-xs text-text-muted">{{ t('government.workspacePage.loggedBy', { name: followup.createdBy }) }}</p>
          </li>
        </ul>
        <BaseButton
          v-if="submissionStore.followups.length > 0"
          size="sm"
          variant="ghost"
          class="mt-3"
          :loading="submissionStore.isFollowupsLoading"
          @click="loadFollowups"
        >
          {{ t('government.workspacePage.refresh') }}
        </BaseButton>
      </Card>

      <Card v-if="canUploadProofOfResponse || submission.proofOfResponse">
        <template #header>
          <h3 class="text-sm font-semibold text-text-primary">{{ t('government.workspacePage.proofOfGovernmentResponse') }}</h3>
        </template>
        <div v-if="submission.proofOfResponse" class="flex flex-col gap-3">
          <div class="flex items-center justify-between gap-3">
            <span class="text-sm text-text-secondary">
              {{ submission.proofOfResponse.originalFilename }}
              &middot; {{ submission.proofOfResponse.fileSizeLabel }}
              &middot;
              {{
                t('government.workspacePage.uploadedByLine', {
                  date: formatDate(submission.proofOfResponse.uploadDate),
                  user: submission.proofOfResponse.uploadedBy,
                })
              }}
            </span>
            <BaseButton variant="secondary" size="sm" @click="downloadProofOfResponse">{{ t('government.workspacePage.download') }}</BaseButton>
          </div>
          <StatusBadge
            :label="t('government.workspacePage.responseOutcome', { outcome: outcomeLabel(submission.responseOutcome) })"
            :variant="submission.responseOutcome === 'Approved' ? 'success' : submission.responseOutcome === 'Rejected' ? 'danger' : 'warning'"
          />
        </div>
        <div v-else class="flex flex-col gap-2">
          <p class="text-sm text-text-secondary">
            {{ t('government.workspacePage.governmentResponseNotice') }}
          </p>
          <BaseButton size="sm" :icon="Upload" class="self-start" @click="openProofOfResponseDialog">
            {{ t('government.workspacePage.uploadProofOfResponse') }}
          </BaseButton>
        </div>

        <div v-if="canMarkComplete" class="mt-4 border-t border-border-light pt-4">
          <BaseButton
            :icon="CircleCheck"
            :loading="submissionStore.isMutating"
            @click="handleMarkComplete"
          >
            {{ t('government.workspacePage.markComplete') }}
          </BaseButton>
        </div>
      </Card>

      <Card v-if="submission.notes">
        <template #header>
          <h3 class="text-sm font-semibold text-text-primary">{{ t('government.workspacePage.notes') }}</h3>
        </template>
        <p class="text-sm text-text-secondary">{{ submission.notes }}</p>
      </Card>
    </template>

    <BaseDialog v-model="isFollowupDialogOpen" :title="t('government.workspacePage.recordFollowUp')" size="sm">
      <div class="flex flex-col gap-4">
        <p class="text-sm text-text-secondary">
          {{ t('government.workspacePage.followUpDialogDescription', { submissionNo }) }}
        </p>
        <DatePicker v-model="followupDate" :label="t('government.workspacePage.followUpDate')" required />
        <TimePicker v-model="followupTime" :label="t('government.workspacePage.followUpTime')" required />
        <TextInput
          v-model="followupContactPerson"
          :label="t('government.workspacePage.followUpContactPerson')"
          :placeholder="t('government.workspacePage.followUpContactPersonPlaceholder')"
          required
        />
        <TextArea
          v-model="followupNotes"
          :label="t('government.workspacePage.followUpNotes')"
          :placeholder="t('government.workspacePage.followUpNotesPlaceholder')"
          :rows="3"
        />
        <div class="flex justify-end gap-2">
          <BaseButton variant="ghost" @click="isFollowupDialogOpen = false">{{ t('common.cancel') }}</BaseButton>
          <BaseButton
            :disabled="!followupDate || !followupTime || !followupContactPerson.trim()"
            :loading="submissionStore.isMutating"
            @click="confirmFollowup"
          >
            {{ t('government.workspacePage.saveFollowUp') }}
          </BaseButton>
        </div>
      </div>
    </BaseDialog>

    <BaseDialog v-model="isProofOfResponseDialogOpen" :title="t('government.workspacePage.uploadProofOfResponse')" size="sm">
      <div class="flex flex-col gap-4">
        <SelectBox v-model="proofOfResponseOutcome" :label="t('government.workspacePage.outcome')" :options="OUTCOME_OPTIONS" />
        <div>
          <label class="mb-1.5 block text-sm font-medium text-text-secondary">{{ t('government.workspacePage.proofOfResponseDocument') }}</label>
          <input
            type="file"
            accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.tiff,.tif"
            class="block w-full text-sm text-text-secondary"
            @change="handleProofOfResponseSelect(($event.target as HTMLInputElement).files?.[0])"
          />
        </div>
        <div class="flex justify-end gap-2">
          <BaseButton variant="ghost" @click="isProofOfResponseDialogOpen = false">{{ t('common.cancel') }}</BaseButton>
          <BaseButton :disabled="!proofOfResponseFile" :loading="submissionStore.isMutating" @click="confirmProofOfResponse">
            {{ t('common.save') }}
          </BaseButton>
        </div>
      </div>
    </BaseDialog>
    <BaseDialog v-model="isWithdrawDialogOpen" :title="t('government.workspacePage.withdrawSubmissionTitle')" size="sm">
      <div class="flex flex-col gap-4">
        <p class="text-sm text-text-secondary">
          {{ t('government.workspacePage.withdrawDialogDescription', { submissionNo }) }}
        </p>
        <TextArea
          v-model="withdrawReason"
          :label="t('government.workspacePage.reasonForWithdrawal')"
          :placeholder="t('government.workspacePage.reasonForWithdrawalPlaceholder')"
          :rows="3"
        />
        <div class="flex justify-end gap-2">
          <BaseButton variant="ghost" @click="isWithdrawDialogOpen = false">{{ t('common.cancel') }}</BaseButton>
          <BaseButton
            variant="danger"
            :disabled="!withdrawReason.trim()"
            :loading="submissionStore.isMutating"
            @click="confirmWithdraw"
          >
            {{ t('government.workspacePage.withdraw') }}
          </BaseButton>
        </div>
      </div>
    </BaseDialog>
  </div>
</template>
