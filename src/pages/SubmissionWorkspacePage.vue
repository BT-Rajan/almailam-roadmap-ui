<script setup lang="ts">
import { ArrowLeft, ArrowRight, Ban, CircleCheck, FileEdit, Pencil, Send, Trash2 } from '@lucide/vue'
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
import RadioGroup from '@/components/common/RadioGroup.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import TimePicker from '@/components/common/TimePicker.vue'
import DocumentPreviewDialog from '@/components/document/DocumentPreviewDialog.vue'
import ProjectFormEntryDialog from '@/components/government/ProjectFormEntryDialog.vue'
import RequiredDocumentChecklist from '@/components/government/RequiredDocumentChecklist.vue'
import InlineConfirmPanel from '@/components/common/InlineConfirmPanel.vue'
import ProjectStageStepper from '@/components/project/ProjectStageStepper.vue'
import SubmissionApprovalStepper from '@/components/government/SubmissionApprovalStepper.vue'
import { useLocale } from '@/composables/useLocale'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { governmentSubmissionService } from '@/services/governmentSubmissionService'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { useProjectFormStore } from '@/stores/projectFormStore'
import { useProjectStore } from '@/stores/projectStore'
import { useToastStore } from '@/stores/toastStore'
import type { ResponseOutcome } from '@/types/Submission'
import type { SelectOption } from '@/types/Ui'
import { triggerBlobDownload } from '@/utils/fileDownload'
import { formatDate } from '@/utils/dateFormatter'
import { getSubmissionOutcomeVariant, getSubmissionStageVariant } from '@/utils/submissionHelpers'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isRtl } = useLocale()

// Points the way "back" actually goes, which flips with reading
// direction.
const backIcon = computed(() => (isRtl.value ? ArrowRight : ArrowLeft))
const submissionStore = useGovernmentSubmissionStore()
const projectStore = useProjectStore()
const projectFormStore = useProjectFormStore()
const toastStore = useToastStore()

const submissionNo = computed(() => route.params.submissionNo as string)
// Present when this page was opened with a specific project in
// context -- the route param on the project-scoped route
// (/projects/:projectId/permit-applications/:submissionNo), else the
// ?projectId= query of the global one. Carried in the URL rather than
// assumed from route history, so a hard refresh or a shared link still
// remembers where "back" goes.
const originProjectId = computed(() => {
  const param = route.params.projectId
  if (typeof param === 'string') return param
  const value = route.query.projectId
  return typeof value === 'string' ? value : undefined
})
// The full project (with the workflow flags/selections the stepper
// needs), only when opened from a project. Not the same as `project`
// below, which is the slimmer record the Permit Applications store keeps.
const originProject = computed(() => (originProjectId.value ? projectStore.getProjectById(originProjectId.value) : undefined))
const isLoading = ref(true)
const loadError = ref<string | undefined>(undefined)

async function loadData(): Promise<void> {
  isLoading.value = true
  loadError.value = undefined
  try {
    if (originProjectId.value && projectStore.projects.length === 0) await projectStore.loadProjects()
    const loaded = await submissionStore.loadSubmissionByNo(submissionNo.value)
    if (loaded) {
      if (loaded.stage === 'Track' || loaded.stage === 'Update' || loaded.stage === 'Close') {
        await submissionStore.loadFollowups(submissionNo.value)
      }
      // Always reload for this submission's own project -- projectFormStore
      // holds one project's entries at a time, and a prior visit to a
      // different project's submission would otherwise leave it stale.
      await projectFormStore.load(loaded.projectId)
    }
  } catch {
    loadError.value = 'Unable to load this permit application.'
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
      label: t('government.workspacePage.detailFiledDate'),
      value: submission.value.submittedDate ? formatDate(submission.value.submittedDate) : t('government.submissionsPage.notSubmitted'),
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

const SUBMISSION_STAGE_LABEL_KEYS: Record<string, string> = {
  Prepare: 'government.submissionStage.prepare',
  Apply: 'government.submissionStage.apply',
  Track: 'government.submissionStage.track',
  Update: 'government.submissionStage.update',
  Close: 'government.submissionStage.close',
}

function submissionStageLabel(stage: string): string {
  const key = SUBMISSION_STAGE_LABEL_KEYS[stage]
  return key ? t(key) : stage
}

// -- Prepare: fill in the form ---------------------------------------------

const formEntry = computed(() => projectFormStore.entries.find((entry) => entry.formId === form.value?.id))
const isFormEntryDialogOpen = ref(false)

function openFormEntryDialog(): void {
  isFormEntryDialogOpen.value = true
}

const isDocumentPreviewOpen = ref(false)

function viewFilledForm(): void {
  if (!formEntry.value?.documentId) return
  isDocumentPreviewOpen.value = true
}

// -- Required documents ---------------------------------------------------

const canUploadDocuments = computed(() => submission.value?.stage === 'Prepare')
const uploadingDocumentId = ref<number>()

async function handleDocumentUpload(documentId: number, file: File): Promise<void> {
  uploadingDocumentId.value = documentId
  const success = await submissionStore.uploadDocument(submissionNo.value, documentId, file)
  uploadingDocumentId.value = undefined
  if (success) {
    toastStore.show('success', t('government.workspacePage.documentUploadedTitle'), t('government.workspacePage.documentUploadedDescription'))
  } else {
    toastStore.show('error', t('common.uploadFailed'), submissionStore.mutationError ?? t('common.pleaseTryAgain'))
  }
}

async function handleDocumentDownload(documentId: number): Promise<void> {
  try {
    const blob = await governmentSubmissionService.downloadDocument(submissionNo.value, documentId)
    const doc = submission.value?.documents.find((d) => d.id === documentId)
    triggerBlobDownload(blob, doc?.originalFilename ?? 'document')
  } catch {
    toastStore.show('error', t('common.downloadFailed'), t('common.pleaseTryAgain'))
  }
}

// -- Confirm readiness (Prepare -> Apply) -----------------------------------

const canConfirmReadiness = computed(() => submission.value?.stage === 'Prepare' && submission.value?.allDocumentsSatisfied === true)

async function handleConfirmReadiness(): Promise<void> {
  const success = await submissionStore.confirmReadiness(submissionNo.value)
  if (success) {
    toastStore.show('success', t('government.workspacePage.readinessConfirmedTitle'), t('government.workspacePage.readinessConfirmedDescription'))
  } else {
    toastStore.show('error', t('government.workspacePage.unableToConfirmReadiness'), submissionStore.mutationError ?? t('common.pleaseTryAgain'))
  }
}

// -- Apply: record acknowledgement (Apply -> Track) -------------------------

const acknowledgementNumber = ref('')
const paymentReference = ref('')
const acknowledgementNotes = ref('')
const acknowledgementFile = ref<File>()

function handleAcknowledgementFileSelect(file: File | undefined): void {
  acknowledgementFile.value = file
}

async function handleRecordAcknowledgement(): Promise<void> {
  const success = await submissionStore.recordAcknowledgement(submissionNo.value, {
    acknowledgementNumber: acknowledgementNumber.value.trim() || undefined,
    paymentReference: paymentReference.value.trim() || undefined,
    notes: acknowledgementNotes.value.trim() || undefined,
    file: acknowledgementFile.value,
  })
  if (success) {
    acknowledgementNumber.value = ''
    paymentReference.value = ''
    acknowledgementNotes.value = ''
    acknowledgementFile.value = undefined
    toastStore.show('success', t('government.workspacePage.applicationFiledTitle'), t('government.workspacePage.applicationFiledDescription', { submissionNo: submissionNo.value }))
  } else {
    toastStore.show('error', t('government.workspacePage.unableToFileApplication'), submissionStore.mutationError ?? t('common.pleaseTryAgain'))
  }
}

async function downloadAcknowledgement(): Promise<void> {
  try {
    const blob = await governmentSubmissionService.downloadAcknowledgement(submissionNo.value)
    triggerBlobDownload(blob, submission.value?.proofOfSubmission?.originalFilename ?? 'acknowledgement')
  } catch {
    toastStore.show('error', t('common.downloadFailed'), t('common.pleaseTryAgain'))
  }
}

// -- Track / Update: contact log --------------------------------------------

const isFollowupDialogOpen = ref(false)
const followupEntryStage = ref<'Track' | 'Update'>('Track')
const followupDate = ref('')
const followupTime = ref('')
const followupContactPerson = ref('')
const followupNotes = ref('')
const followupFile = ref<File>()

const ENTRY_STAGE_OPTIONS = computed<SelectOption[]>(() => [
  { label: 'Track', value: 'Track', labelKey: 'government.workspacePage.entryStageTrack' },
  { label: 'Update', value: 'Update', labelKey: 'government.workspacePage.entryStageUpdate' },
])

function openFollowupDialog(): void {
  followupEntryStage.value = 'Track'
  followupDate.value = new Date().toISOString().slice(0, 10)
  followupTime.value = ''
  followupContactPerson.value = ''
  followupNotes.value = ''
  followupFile.value = undefined
  isFollowupDialogOpen.value = true
}

function handleFollowupFileSelect(file: File | undefined): void {
  followupFile.value = file
}

async function confirmFollowup(): Promise<void> {
  if (!followupDate.value || !followupTime.value || !followupContactPerson.value.trim()) return
  const success = await submissionStore.addFollowup(submissionNo.value, {
    entryStage: followupEntryStage.value,
    followupDate: followupDate.value,
    followupTime: followupTime.value,
    contactPerson: followupContactPerson.value.trim(),
    notes: followupNotes.value.trim() || undefined,
    file: followupEntryStage.value === 'Update' ? followupFile.value : undefined,
  })
  if (success) {
    isFollowupDialogOpen.value = false
    toastStore.show('success', t('government.workspacePage.followUpRecordedTitle'), t('government.workspacePage.followUpRecordedDescription'))
  } else {
    toastStore.show('error', t('government.workspacePage.unableToRecordFollowUp'), submissionStore.mutationError ?? t('common.pleaseTryAgain'))
  }
}

async function downloadFollowupDocument(followupId: string, originalFilename: string | undefined): Promise<void> {
  try {
    const blob = await governmentSubmissionService.downloadFollowupDocument(submissionNo.value, followupId)
    triggerBlobDownload(blob, originalFilename ?? 'document')
  } catch {
    toastStore.show('error', t('common.downloadFailed'), t('common.pleaseTryAgain'))
  }
}

const canLogContact = computed(() => submission.value?.stage === 'Track' || submission.value?.stage === 'Update')

// -- Close: final outcome ----------------------------------------------------

const canClose = computed(() => !!submission.value && submission.value.stage !== 'Close')

// -- Edit / Delete ---------------------------------------------------------
// A closed application is a finished record -- it can be deleted (by
// someone with that permission) but no longer edited.
const canEdit = computed(() => !!submission.value && submission.value.stage !== 'Close')

function goEdit(): void {
  if (originProjectId.value) {
    router.push({ name: ROUTE_NAMES.PROJECT_SUBMISSION_EDIT, params: { projectId: originProjectId.value, submissionNo: submissionNo.value } })
    return
  }
  router.push({ name: ROUTE_NAMES.SUBMISSION_EDIT, params: { submissionNo: submissionNo.value } })
}

const isDeleteConfirmOpen = ref(false)
const isDeleting = ref(false)

const deleteConfirmMessage = computed(() => {
  const base = t('government.workspacePage.deleteConfirmMessage')
  // Once it's been filed there's a real record with the authority --
  // point at Withdrawn as the way to keep it.
  return submission.value && submission.value.stage !== 'Prepare'
    ? `${base} ${t('government.workspacePage.deleteConfirmMessageFiled')}`
    : base
})

async function handleConfirmDelete(): Promise<void> {
  isDeleting.value = true
  try {
    await submissionStore.deleteSubmission(submissionNo.value)
    toastStore.show(
      'success',
      t('government.submissionsPage.submissionDeletedTitle'),
      t('government.submissionsPage.submissionDeletedDescription', { no: submissionNo.value }),
    )
    goBack()
  } catch (error) {
    toastStore.show('error', t('government.submissionsPage.failedToDeleteSubmission'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
    isDeleteConfirmOpen.value = false
  } finally {
    isDeleting.value = false
  }
}
const isCloseDialogOpen = ref(false)
const closeOutcome = ref<ResponseOutcome>('Approved')
const closingNotes = ref('')
const closeFile = ref<File>()

const OUTCOME_OPTIONS = computed<SelectOption[]>(() => [
  { label: 'Approved', value: 'Approved', labelKey: 'government.responseOutcome.approved' },
  { label: 'Rejected', value: 'Rejected', labelKey: 'government.responseOutcome.rejected' },
  { label: 'No Response', value: 'No Response', labelKey: 'government.responseOutcome.noResponse' },
  { label: 'Withdrawn', value: 'Withdrawn', labelKey: 'government.responseOutcome.withdrawn' },
])

const OUTCOME_LABEL_KEYS: Record<string, string> = {
  Approved: 'government.responseOutcome.approved',
  Rejected: 'government.responseOutcome.rejected',
  'No Response': 'government.responseOutcome.noResponse',
  Withdrawn: 'government.responseOutcome.withdrawn',
}

function outcomeLabel(outcome: string | null | undefined): string {
  if (!outcome) return ''
  const key = OUTCOME_LABEL_KEYS[outcome]
  return key ? t(key) : outcome
}

function openCloseDialog(): void {
  closeOutcome.value = 'Approved'
  closingNotes.value = ''
  closeFile.value = undefined
  isCloseDialogOpen.value = true
}

function handleCloseFileSelect(file: File | undefined): void {
  closeFile.value = file
}

async function confirmClose(): Promise<void> {
  if (!closingNotes.value.trim()) return
  const projectId = submission.value?.projectId
  const success = await submissionStore.closeApplication(submissionNo.value, {
    outcome: closeOutcome.value,
    closingNotes: closingNotes.value.trim(),
    file: closeFile.value,
  })
  if (success) {
    isCloseDialogOpen.value = false
    toastStore.show('success', t('government.workspacePage.applicationClosedTitle'), t('government.workspacePage.applicationClosedDescription', { submissionNo: submissionNo.value }))
    // An Approved close can advance the project's own workflow stage
    // server-side -- refresh so the project's cached stage (used by the
    // header/stepper if the user navigates back) isn't left stale.
    if (projectId) await projectStore.refreshProject(projectId)
  } else {
    toastStore.show('error', t('government.workspacePage.unableToCloseApplication'), submissionStore.mutationError ?? t('common.pleaseTryAgain'))
  }
}

async function downloadPermitDocument(): Promise<void> {
  try {
    const blob = await governmentSubmissionService.downloadPermitDocument(submissionNo.value)
    triggerBlobDownload(blob, submission.value?.proofOfResponse?.originalFilename ?? 'permit-document')
  } catch {
    toastStore.show('error', t('common.downloadFailed'), t('common.pleaseTryAgain'))
  }
}

function goBack(): void {
  if (originProjectId.value) {
    // Back to the Approvals & Permits card this was opened from.
    router.push({
      name: ROUTE_NAMES.PROJECT_WORKSPACE,
      params: { projectId: originProjectId.value },
      query: { tab: 'government', view: 'overview' },
    })
    return
  }
  router.push({ name: ROUTE_NAMES.GOVERNMENT_SUBMISSIONS })
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <ProjectStageStepper v-if="originProject" :project="originProject" />
    <BaseButton v-else variant="ghost" size="sm" :icon="backIcon" class="self-start no-print" @click="goBack">
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
      <InlineConfirmPanel
        v-if="isDeleteConfirmOpen"
        :title="t('government.workspacePage.deleteConfirmTitle', { no: submission.submissionNo })"
        :message="deleteConfirmMessage"
        :confirm-label="t('government.workspacePage.deleteApplication')"
        :loading="isDeleting"
        @confirm="handleConfirmDelete"
        @cancel="isDeleteConfirmOpen = false"
      />

      <div class="flex flex-col gap-3 tablet:flex-row tablet:items-center tablet:justify-between">
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ authority?.name ?? t('government.unknownAuthority') }} &middot; {{ form?.title ?? t('government.unknownForm') }}</p>
          <h1 class="text-xl font-semibold text-text-primary">{{ submission.submissionNo }}</h1>
        </div>
        <div class="flex items-center gap-2">
          <StatusBadge :label="submissionStageLabel(submission.stage)" :variant="getSubmissionStageVariant(submission.stage)" />
          <BaseButton v-if="canEdit" size="sm" variant="secondary" :icon="Pencil" class="no-print" @click="goEdit">
            {{ t('government.workspacePage.editApplication') }}
          </BaseButton>
          <BaseButton size="sm" variant="secondary" :icon="Trash2" class="no-print" @click="isDeleteConfirmOpen = true">
            {{ t('government.workspacePage.deleteApplication') }}
          </BaseButton>
          <BaseButton v-if="canClose" size="sm" variant="danger" :icon="Ban" @click="openCloseDialog">
            {{ t('government.workspacePage.closeApplication') }}
          </BaseButton>
        </div>
      </div>

      <Card>
        <SubmissionApprovalStepper :stage="submission.stage" :response-outcome="submission.responseOutcome" />
      </Card>

      <Card>
        <template #header>
          <h3 class="text-sm font-semibold text-text-primary">{{ t('government.workspacePage.submissionDetails') }}</h3>
        </template>
        <DetailPanel :title="t('government.workspacePage.submissionDetails')" :items="submissionDetails" />
      </Card>

      <Card>
        <template #header>
          <h3 class="text-sm font-semibold text-text-primary">{{ t('government.workspacePage.prepareTheApplication') }}</h3>
        </template>
        <div class="flex flex-col gap-4">
          <div class="flex flex-wrap items-center justify-between gap-3 rounded-lg bg-bg-secondary p-3">
            <span class="text-sm text-text-secondary">
              {{ formEntry ? t('government.workspacePage.formFilledIn') : t('government.workspacePage.formNotFilledInYet') }}
            </span>
            <div class="flex items-center gap-2 no-print">
              <BaseButton v-if="formEntry" variant="secondary" size="sm" @click="viewFilledForm">{{ t('common.view') }}</BaseButton>
              <BaseButton variant="secondary" size="sm" :icon="FileEdit" @click="openFormEntryDialog">
                {{ formEntry ? t('common.edit') : t('government.workspacePage.fillForm') }}
              </BaseButton>
            </div>
          </div>

          <RequiredDocumentChecklist
            :documents="submission.documents"
            :can-upload="canUploadDocuments"
            :uploading-document-id="uploadingDocumentId"
            @upload="handleDocumentUpload"
            @download="handleDocumentDownload"
          />

          <template v-if="submission.stage === 'Prepare'">
            <p v-if="!canConfirmReadiness" class="text-xs text-text-muted">
              {{ t('government.workspacePage.uploadDocumentsNotice') }}
            </p>
            <BaseButton
              v-else
              :icon="CircleCheck"
              class="self-start"
              :loading="submissionStore.isMutating"
              @click="handleConfirmReadiness"
            >
              {{ t('government.workspacePage.confirmReadiness') }}
            </BaseButton>
          </template>
          <p v-else-if="submission.readinessConfirmedAt" class="text-xs text-text-muted">
            {{ t('government.workspacePage.readinessConfirmedOn', { date: formatDate(submission.readinessConfirmedAt) }) }}
          </p>
        </div>
      </Card>

      <Card v-if="submission.stage === 'Apply'">
        <template #header>
          <h3 class="text-sm font-semibold text-text-primary">{{ t('government.workspacePage.fileTheApplication') }}</h3>
        </template>
        <div class="flex flex-col gap-4">
          <p class="text-sm text-text-secondary">{{ t('government.workspacePage.fileApplicationNotice') }}</p>
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <TextInput v-model="acknowledgementNumber" :label="t('government.workspacePage.acknowledgementNumber')" :placeholder="t('government.workspacePage.acknowledgementNumberPlaceholder')" />
            <TextInput v-model="paymentReference" :label="t('government.workspacePage.paymentReference')" :placeholder="t('government.workspacePage.paymentReferencePlaceholder')" />
          </div>
          <TextArea v-model="acknowledgementNotes" :label="t('common.notes')" :rows="2" />
          <div>
            <label class="mb-1.5 block text-sm font-medium text-text-secondary">{{ t('government.workspacePage.acknowledgementDocument') }}</label>
            <input
              type="file"
              accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.tiff,.tif"
              class="block w-full text-sm text-text-secondary"
              @change="handleAcknowledgementFileSelect(($event.target as HTMLInputElement).files?.[0])"
            />
          </div>
          <BaseButton :icon="Send" class="self-start" :loading="submissionStore.isMutating" @click="handleRecordAcknowledgement">
            {{ t('government.workspacePage.recordAcknowledgement') }}
          </BaseButton>
        </div>
      </Card>

      <Card v-if="submission.proofOfSubmission || submission.acknowledgementNumber">
        <template #header>
          <h3 class="text-sm font-semibold text-text-primary">{{ t('government.workspacePage.filingDetails') }}</h3>
        </template>
        <div class="flex flex-col gap-2 text-sm text-text-secondary">
          <p v-if="submission.acknowledgementNumber">{{ t('government.workspacePage.acknowledgementNumberLine', { value: submission.acknowledgementNumber }) }}</p>
          <p v-if="submission.paymentReference">{{ t('government.workspacePage.paymentReferenceLine', { value: submission.paymentReference }) }}</p>
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
            <BaseButton variant="secondary" size="sm" @click="downloadAcknowledgement">{{ t('government.workspacePage.download') }}</BaseButton>
          </div>
        </div>
      </Card>

      <Card v-if="canLogContact || submissionStore.followups.length > 0">
        <template #header>
          <div class="flex items-center justify-between">
            <h3 class="text-sm font-semibold text-text-primary">{{ t('government.workspacePage.followUpLog') }}</h3>
            <BaseButton v-if="canLogContact" size="sm" variant="secondary" @click="openFollowupDialog">
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
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-text-primary">{{ followup.contactPerson }}</span>
                <StatusBadge :label="followup.stage === 'Update' ? t('government.workspacePage.entryStageUpdate') : t('government.workspacePage.entryStageTrack')" variant="neutral" size="sm" />
              </div>
              <span class="text-xs text-text-muted">{{
                t('government.workspacePage.followUpAt', { date: formatDate(followup.followupDate), time: followup.followupTime })
              }}</span>
            </div>
            <p v-if="followup.notes" class="text-sm text-text-secondary">{{ followup.notes }}</p>
            <div v-if="followup.document" class="flex items-center gap-2 text-xs text-text-muted">
              <span>{{ followup.document.originalFilename }} &middot; {{ followup.document.fileSizeLabel }}</span>
              <button type="button" class="font-medium text-primary-600 hover:text-primary-700" @click="downloadFollowupDocument(followup.id, followup.document.originalFilename)">
                {{ t('common.download') }}
              </button>
            </div>
            <p class="text-xs text-text-muted">{{ t('government.workspacePage.loggedBy', { name: followup.createdBy }) }}</p>
          </li>
        </ul>
      </Card>

      <Card v-if="submission.stage === 'Close'">
        <template #header>
          <h3 class="text-sm font-semibold text-text-primary">{{ t('government.workspacePage.closingDetails') }}</h3>
        </template>
        <div class="flex flex-col gap-3">
          <StatusBadge
            :label="t('government.workspacePage.responseOutcome', { outcome: outcomeLabel(submission.responseOutcome) })"
            :variant="getSubmissionOutcomeVariant(submission.responseOutcome)"
          />
          <p v-if="submission.closingNotes" class="text-sm text-text-secondary">{{ submission.closingNotes }}</p>
          <div v-if="submission.proofOfResponse" class="flex items-center justify-between gap-3">
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
            <BaseButton variant="secondary" size="sm" @click="downloadPermitDocument">{{ t('government.workspacePage.download') }}</BaseButton>
          </div>
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
        <RadioGroup v-model="followupEntryStage" :label="t('government.workspacePage.entryStage')" :options="ENTRY_STAGE_OPTIONS" :vertical="false" />
        <p class="-mt-2 text-xs text-text-muted">
          {{ followupEntryStage === 'Update' ? t('government.workspacePage.entryStageUpdateHint') : t('government.workspacePage.entryStageTrackHint') }}
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
        <div v-if="followupEntryStage === 'Update'">
          <label class="mb-1.5 block text-sm font-medium text-text-secondary">{{ t('government.workspacePage.followUpDocument') }}</label>
          <input
            type="file"
            accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.tiff,.tif"
            class="block w-full text-sm text-text-secondary"
            @change="handleFollowupFileSelect(($event.target as HTMLInputElement).files?.[0])"
          />
        </div>
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

    <BaseDialog v-model="isCloseDialogOpen" :title="t('government.workspacePage.closeApplicationTitle')" size="sm">
      <div class="flex flex-col gap-4">
        <p class="text-sm text-text-secondary">
          {{ t('government.workspacePage.closeDialogDescription', { submissionNo }) }}
        </p>
        <SelectBox v-model="closeOutcome" :label="t('government.workspacePage.outcome')" :options="OUTCOME_OPTIONS" />
        <TextArea
          v-model="closingNotes"
          :label="t('government.workspacePage.closingNotes')"
          :placeholder="t('government.workspacePage.closingNotesPlaceholder')"
          :rows="3"
          required
        />
        <div>
          <label class="mb-1.5 block text-sm font-medium text-text-secondary">{{ t('government.workspacePage.permitDocument') }}</label>
          <input
            type="file"
            accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.tiff,.tif"
            class="block w-full text-sm text-text-secondary"
            @change="handleCloseFileSelect(($event.target as HTMLInputElement).files?.[0])"
          />
        </div>
        <div class="flex justify-end gap-2">
          <BaseButton variant="ghost" @click="isCloseDialogOpen = false">{{ t('common.cancel') }}</BaseButton>
          <BaseButton
            variant="danger"
            :disabled="!closingNotes.trim()"
            :loading="submissionStore.isMutating"
            @click="confirmClose"
          >
            {{ t('government.workspacePage.closeApplication') }}
          </BaseButton>
        </div>
      </div>
    </BaseDialog>

    <ProjectFormEntryDialog
      v-if="submission && form"
      v-model="isFormEntryDialogOpen"
      :project-id="submission.projectId"
      :form="form"
      :entry="formEntry"
    />
    <DocumentPreviewDialog v-model="isDocumentPreviewOpen" :document-id="formEntry?.documentId ?? undefined" />
  </div>
</template>
