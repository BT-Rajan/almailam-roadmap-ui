<script setup lang="ts">
import { AlertTriangle, MessageSquare } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import DetailPanel from '@/components/common/DetailPanel.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import FillGovernmentFormDialog from '@/components/government/FillGovernmentFormDialog.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useClientStore } from '@/stores/clientStore'
import { useContractStore } from '@/stores/contractStore'
import { useDocumentStore } from '@/stores/documentStore'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { usePaymentStore } from '@/stores/paymentStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useToastStore } from '@/stores/toastStore'
import type { AgreementStream } from '@/types/Payment'
import type { Client } from '@/types/Client'
import type { GovernmentForm } from '@/types/Government'
import type { Project, ProjectWorkspaceTabKey, WorkflowStage } from '@/types/Project'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { getClientVerificationVariant } from '@/utils/clientHelpers'
import { getDocumentStatusVariant } from '@/utils/documentHelpers'
import { formMatchesProjectService } from '@/utils/governmentFormHelpers'
import { getAgreementStreamLabel } from '@/utils/paymentHelpers'
import { getSubmissionStatusVariant } from '@/utils/submissionHelpers'
import { getWorkflowStageLabel, hasProjectPassedStage } from '@/utils/projectHelpers'

const props = defineProps<{
  project: Project
  client: Client | undefined
  // Which stage's overview to show -- the stage section currently being
  // navigated to via the Workflow Progress stepper, NOT necessarily
  // project.currentStage. The stepper deliberately lets staff jump to
  // any stage's view regardless of where the project really is (e.g.
  // drafting a quotation early, or reviewing a past stage), so basing
  // this on currentStage directly meant Overview showed the wrong
  // stage's content while looking at a different one. See
  // ProjectWorkspacePage.vue's stageContext for how this is derived.
  stageContext: WorkflowStage
}>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
}>()

const router = useRouter()
const clientStore = useClientStore()
const quotationStore = useQuotationStore()
const paymentStore = usePaymentStore()
const contractStore = useContractStore()
const documentStore = useDocumentStore()
const governmentSubmissionStore = useGovernmentSubmissionStore()
const toastStore = useToastStore()
const { t } = useI18n()

// Scope, Project Details, and Client Details are only useful while the
// project is still being set up -- once it's past Quotation, staff are
// working from that stage's own overview card instead, and repeating this
// same block on every stage's Overview was reported as noise.
const showScopeAndDetails = computed(() => props.stageContext === 'Requirement' || props.stageContext === 'Quotation')

const STAGE_LABEL_KEYS: Record<string, string> = {
  Requirement: 'project.stage.requirement',
  Quotation: 'project.stage.quotation',
  'Payment Plan': 'project.stage.paymentPlan',
  Contract: 'project.stage.contract',
  Design: 'project.stage.design',
  Supervision: 'project.stage.supervision',
  'Government Submission': 'project.stage.governmentSubmission',
}
function stageLabel(stage: string): string {
  return t(STAGE_LABEL_KEYS[stage] ?? getWorkflowStageLabel(stage))
}

const PRIORITY_LABEL_KEYS: Record<string, string> = {
  High: 'project.priority.high',
  Medium: 'project.priority.medium',
  Low: 'project.priority.low',
}
function priorityLabel(priority: string): string {
  return t(PRIORITY_LABEL_KEYS[priority] ?? priority)
}

const projectDetailItems = computed(() => [
  { label: t('project.overviewTab.fields.service'), value: props.project.service },
  { label: t('project.overviewTab.fields.fieldEngineer'), value: props.project.engineer },
  { label: t('project.overviewTab.fields.startDate'), value: formatDate(props.project.startDate) },
  { label: t('project.overviewTab.fields.targetCompletionDate'), value: formatDate(props.project.targetDate) },
  { label: t('project.overviewTab.fields.currentStage'), value: stageLabel(props.project.currentStage) },
  { label: t('project.overviewTab.fields.priority'), value: priorityLabel(props.project.priority) },
])

const clientDetailItems = computed(() => {
  if (!props.client) return []
  return [
    { label: t('project.overviewTab.fields.companyName'), value: props.client.companyName },
    { label: t('project.overviewTab.fields.contactPerson'), value: props.client.contactPerson },
    { label: t('project.overviewTab.fields.mobile'), value: props.client.mobile },
    { label: t('project.overviewTab.fields.email'), value: props.client.email },
    { label: t('project.overviewTab.fields.city'), value: props.client.city },
  ]
})

const hasScope = computed(
  () =>
    Boolean(props.project.description) ||
    (props.project.selectedActivities && props.project.selectedActivities.length > 0) ||
    (props.project.selectedSupervisionActivities && props.project.selectedSupervisionActivities.length > 0),
)

// Civil ID verification (Quotation), design document status (Design), and
// the approvals/permits checklist (Government Submission) all need data
// that isn't loaded anywhere else in the project workspace by default --
// fetched only when their card is actually showing, not on every visit to
// this tab regardless of stage context.
function loadStageDataIfNeeded(): void {
  if ((props.stageContext === 'Requirement' || props.stageContext === 'Quotation') && props.client) {
    clientStore.loadClientDetail(props.client.id)
  }
  if (props.stageContext === 'Design' && documentStore.documents.length === 0) {
    documentStore.loadDocuments()
  }
  if (props.stageContext === 'Government Submission') {
    if (governmentSubmissionStore.submissions.length === 0) governmentSubmissionStore.loadSubmissions()
    if (documentStore.documents.length === 0) documentStore.loadDocuments()
  }
}
onMounted(loadStageDataIfNeeded)
watch(() => [props.stageContext, props.client?.id], loadStageDataIfNeeded)

// Civil ID is filed under the 'Identity Document' category regardless of
// the client's actual document-type label -- see
// getDocumentCategoryForIdentificationType (constants/clientOptions.ts).
const civilIdDocument = computed(() => clientStore.documents.find((document) => document.category === 'Identity Document'))

// Mirrors ProjectRequirementTab's own check exactly (and the backend's
// real Requirement -> Quotation exit criterion,
// project_service._assert_stage_exit_criteria) -- a ClientIdentification
// record on file, not just any uploaded document. This tab is the one
// staff land on by default while a project sits at Requirement (the top
// tab bar shows only "Overview" for that stage -- see
// ProjectWorkspacePage.vue's TABS), so the "ready to advance" state has
// to be visible here, not only on the Requirement tab itself which
// needs an extra click via the Workflow Progress stepper to reach.
const hasClientIdentification = computed(() => clientStore.identifications.length > 0)

function viewCivilIdDocument(): void {
  if (!props.client || !civilIdDocument.value) return
  clientStore.viewDocument(props.client.id, civilIdDocument.value.id).catch(() => {
    toastStore.show('error', 'Failed to open document', 'Please try again.')
  })
}

const latestQuotation = computed(() => quotationStore.latestQuotation)

// The quotation the payment plan is built against -- the one Approved
// quotation, same fact the Payment Plan stage's own entry criterion
// checks server-side (project_service._assert_stage_exit_criteria).
const paymentPlanQuotation = computed(() => quotationStore.quotations.find((quotation) => quotation.status === 'Approved'))

// One row per billing stream this project actually includes, each with
// its financial agreement if one has been created yet -- mirrors
// usePaymentAgreements' own visibleStreams/agreementForStream.
const paymentPlanAgreements = computed(() => {
  const streams: AgreementStream[] = []
  if (props.project.includesDesign) streams.push('Design')
  if (props.project.includesSupervision) streams.push('Supervision')
  return streams.map((stream) => ({ stream, agreement: paymentStore.getAgreementByProject(props.project.id, stream) }))
})

// The contract's own linked quotation (contract.quotationNo) rather than
// quotationStore.latestQuotation -- once a contract exists it should
// always point at exactly the quotation it was generated from, not
// whichever quotation happens to be newest (a later draft revision could
// otherwise show here despite never having been the one approved).
const latestContract = computed(() => contractStore.latestContract)
const contractQuotation = computed(() =>
  latestContract.value?.quotationNo
    ? quotationStore.quotations.find((quotation) => quotation.quotationNo === latestContract.value?.quotationNo)
    : undefined,
)

// Design deliverables -- documents of type 'Drawing' added against this
// project (see ProjectDocumentsTab.vue's mode="design").
const designDocuments = computed(() => documentStore.documentsByProject(props.project.id).filter((document) => document.type === 'Drawing'))

// Required Documents -- every fillable government form the Service
// Document Map (Administration) says this project's service needs (see
// governmentFormHelpers.formMatchesProjectService), each checked against
// a real generated document via source_form_id rather than guessing from
// a title -- the single source of truth for "what does this project need
// to prepare", replacing the separate name-matched Design checklist and
// the Documents tab's service-tag "suggested forms" preview list that
// used to duplicate this same question two different, looser ways.
const requiredForms = computed<GovernmentForm[]>(() =>
  governmentSubmissionStore.forms.filter(
    (form) => form.status === 'Active' && Boolean(form.template) && formMatchesProjectService(form, props.project.service),
  ),
)

function filledDocumentFor(form: GovernmentForm) {
  return documentStore.documentsByProject(props.project.id).find((document) => document.sourceFormId === form.id)
}

const isFillDialogOpen = ref(false)
const fillDialogForm = ref<GovernmentForm | undefined>(undefined)

function openFillDialog(form: GovernmentForm): void {
  fillDialogForm.value = form
  isFillDialogOpen.value = true
}

function viewFilledDocument(documentId: string): void {
  router.push({ name: ROUTE_NAMES.DOCUMENT_VIEWER, params: { documentId } })
}

// Approvals & Permits (Government Submission) checklist -- every
// submission filed for this project, with a computed "last worked on"
// date. GovernmentSubmission has no updatedAt field of its own, so this
// takes the most recent of decisionDate/submittedDate as the closest
// available proxy.
const governmentSubmissions = computed(() => governmentSubmissionStore.submissionsByProject(props.project.id))

function lastWorkedOnDate(submission: (typeof governmentSubmissions.value)[number]): string | undefined {
  const dates = [submission.decisionDate, submission.submittedDate].filter((value): value is string => Boolean(value))
  if (dates.length === 0) return undefined
  return dates.reduce((latest, current) => (new Date(current) > new Date(latest) ? current : latest))
}

const SCOPE_STATUS_LABEL_KEYS: Record<string, string> = {
  Draft: 'project.scopeStatus.draft',
  Approved: 'project.scopeStatus.approved',
}
function scopeStatusLabel(status: string): string {
  return t(SCOPE_STATUS_LABEL_KEYS[status] ?? status)
}

const QUOTATION_STATUS_LABEL_KEYS: Record<string, string> = {
  Draft: 'project.quotationStatus.draft',
  Approved: 'project.quotationStatus.approved',
  Rejected: 'project.quotationStatus.rejected',
  Expired: 'project.quotationStatus.expired',
}
function quotationStatusLabel(status: string): string {
  return t(QUOTATION_STATUS_LABEL_KEYS[status] ?? status)
}

const AGREEMENT_STATUS_LABEL_KEYS: Record<string, string> = {
  Draft: 'project.agreementStatus.draft',
  Approved: 'project.agreementStatus.approved',
}
function agreementStatusLabel(status: string): string {
  return t(AGREEMENT_STATUS_LABEL_KEYS[status] ?? status)
}

const DOCUMENT_STATUS_LABEL_KEYS: Record<string, string> = {
  Draft: 'project.documentStatus.draft',
  'Under Review': 'project.documentStatus.underReview',
  Approved: 'project.documentStatus.approved',
  Rejected: 'project.documentStatus.rejected',
}
function documentStatusLabel(status: string): string {
  return t(DOCUMENT_STATUS_LABEL_KEYS[status] ?? status)
}

const SUBMISSION_STATUS_LABEL_KEYS: Record<string, string> = {
  Draft: 'project.submissionStatus.draft',
  Submitted: 'project.submissionStatus.submitted',
  'Under Review': 'project.submissionStatus.underReview',
  'Comments Received': 'project.submissionStatus.commentsReceived',
  Approved: 'project.submissionStatus.approved',
  Rejected: 'project.submissionStatus.rejected',
  Withdrawn: 'project.submissionStatus.withdrawn',
}
function submissionStatusLabel(status: string): string {
  return t(SUBMISSION_STATUS_LABEL_KEYS[status] ?? status)
}

const VERIFICATION_RESULT_LABEL_KEYS: Record<string, string> = {
  Verified: 'clientOptions.verificationResult.verified',
  Rejected: 'clientOptions.verificationResult.rejected',
  Pending: 'clientOptions.verificationResult.pending',
}
function verificationResultLabel(result: string): string {
  return t(VERIFICATION_RESULT_LABEL_KEYS[result] ?? result)
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <Card v-if="hasScope && showScopeAndDetails">
      <template #header>
        <h3 class="text-sm font-semibold text-text-primary">{{ t('project.overviewTab.scopeTitle') }}</h3>
      </template>
      <p v-if="project.description" class="whitespace-pre-wrap text-sm text-text-secondary">{{ project.description }}</p>

      <div v-if="project.selectedActivities && project.selectedActivities.length > 0" class="mt-3 border-t border-border-light pt-3">
        <p class="mb-1.5 text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.overviewTab.servicesLabel') }}</p>
        <ul class="flex flex-col gap-1">
          <li
            v-for="item in project.selectedActivities"
            :key="item.activityId"
            class="flex items-center justify-between gap-3 text-sm text-text-secondary"
          >
            <span>{{ item.activityName }}</span>
            <span class="shrink-0 text-text-muted">{{ formatCurrency(item.fixedCost) }}</span>
          </li>
        </ul>
      </div>

      <div v-if="project.selectedSupervisionActivities && project.selectedSupervisionActivities.length > 0" class="mt-3 border-t border-border-light pt-3">
        <p class="mb-1.5 text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.overviewTab.supervisionMonthlyLabel') }}</p>
        <p class="mb-1.5 text-xs text-text-muted">
          {{ project.supervisionStartDate ? formatDate(project.supervisionStartDate) : t('project.overviewTab.notSet') }} –
          {{ project.supervisionEndDate ? formatDate(project.supervisionEndDate) : t('project.overviewTab.ongoing') }}
        </p>
        <ul class="flex flex-col gap-1">
          <li
            v-for="item in project.selectedSupervisionActivities"
            :key="item.activityId"
            class="flex items-center justify-between gap-3 text-sm text-text-secondary"
          >
            <span>{{ item.activityName }} ({{ formatDate(item.startDate) }} – {{ item.endDate ? formatDate(item.endDate) : t('project.overviewTab.ongoing') }})</span>
            <span class="shrink-0 text-text-muted">{{ formatCurrency(item.monthlyRate) }}/mo</span>
          </li>
        </ul>
      </div>
    </Card>

    <Card v-if="stageContext === 'Requirement'">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h3 class="text-sm font-semibold text-text-primary">{{ t('project.overviewTab.requirementTitle') }}</h3>
          <div class="flex items-center gap-2 no-print">
            <BaseButton
              v-if="project.scopeStatus === 'Approved' && hasClientIdentification && !hasProjectPassedStage(project.currentStage, 'Quotation')"
              size="sm"
              @click="emit('navigate-tab', 'quotation')"
            >
              {{ t('project.overviewTab.advanceToQuotation') }}
            </BaseButton>
            <BaseButton variant="secondary" size="sm" @click="emit('navigate-tab', 'requirement')">{{ t('project.overviewTab.goToRequirement') }}</BaseButton>
          </div>
        </div>
      </template>
      <div class="flex flex-col gap-4">
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm text-text-secondary">{{ t('project.overviewTab.scopeOfWorkStatus') }}</span>
          <StatusBadge
            :label="scopeStatusLabel(project.scopeStatus)"
            :variant="project.scopeStatus === 'Approved' ? 'success' : 'neutral'"
          />
        </div>

        <div
          v-if="project.scopeStatus === 'Approved' && !hasClientIdentification"
          class="flex items-center gap-2 rounded-lg border border-warning-100 bg-warning-50 px-3 py-2.5 text-sm text-warning-700"
        >
          <AlertTriangle class="h-4 w-4 shrink-0" />
          <span>{{ t('project.overviewTab.noClientIdWarning') }}</span>
        </div>
      </div>
    </Card>

    <Card v-if="stageContext === 'Quotation'">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h3 class="text-sm font-semibold text-text-primary">{{ t('project.overviewTab.quotationTitle') }}</h3>
          <BaseButton variant="secondary" size="sm" class="no-print" @click="emit('navigate-tab', 'quotation')">{{ t('project.overviewTab.goToQuotation') }}</BaseButton>
        </div>
      </template>
      <div class="flex flex-col gap-4">
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm text-text-secondary">{{ t('project.overviewTab.quotationStatusLabel') }}</span>
          <StatusBadge
            v-if="latestQuotation"
            :label="quotationStatusLabel(latestQuotation.status)"
            :variant="latestQuotation.status === 'Approved' ? 'success' : latestQuotation.status === 'Rejected' ? 'danger' : 'neutral'"
          />
          <span v-else class="text-sm text-text-muted">{{ t('project.overviewTab.noQuotationYet') }}</span>
        </div>

        <div class="flex flex-col items-start justify-between gap-3 rounded-lg border border-warning-100 bg-warning-50 px-3 py-2.5 tablet:flex-row tablet:items-center">
          <div class="flex items-center gap-2 text-sm text-warning-700">
            <AlertTriangle class="h-4 w-4 shrink-0" />
            <span>{{ t('project.overviewTab.civilIdMustLabel') }}</span>
            <StatusBadge
              v-if="civilIdDocument"
              :label="verificationResultLabel(civilIdDocument.verificationStatus)"
              :variant="getClientVerificationVariant(civilIdDocument.verificationStatus)"
            />
            <span v-else class="text-warning-700">{{ t('project.overviewTab.notUploadedYet') }}</span>
          </div>
          <BaseButton v-if="civilIdDocument" variant="ghost" size="sm" class="no-print" @click="viewCivilIdDocument">
            {{ t('project.overviewTab.viewCivilId') }}
          </BaseButton>
        </div>
      </div>
    </Card>

    <Card v-if="stageContext === 'Payment Plan'">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h3 class="text-sm font-semibold text-text-primary">{{ t('project.overviewTab.paymentPlanTitle') }}</h3>
          <BaseButton variant="secondary" size="sm" class="no-print" @click="emit('navigate-tab', 'payment-plan')">{{ t('project.overviewTab.goToPaymentPlan') }}</BaseButton>
        </div>
      </template>
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
          <div>
            <p class="text-xs text-text-muted">{{ t('project.overviewTab.quotationNumber') }}</p>
            <p class="text-sm font-medium text-text-primary">{{ paymentPlanQuotation?.quotationNo ?? '—' }}</p>
          </div>
          <div>
            <p class="text-xs text-text-muted">{{ t('project.overviewTab.quotationDate') }}</p>
            <p class="text-sm font-medium text-text-primary">{{ paymentPlanQuotation ? formatDate(paymentPlanQuotation.issueDate) : '—' }}</p>
          </div>
          <div>
            <p class="text-xs text-text-muted">{{ t('project.overviewTab.quotationAmount') }}</p>
            <p class="text-sm font-medium text-text-primary">{{ paymentPlanQuotation ? formatCurrency(paymentPlanQuotation.amount) : '—' }}</p>
          </div>
        </div>

        <div v-if="paymentPlanAgreements.length > 0" class="flex flex-col gap-2">
          <div
            v-for="row in paymentPlanAgreements"
            :key="row.stream"
            class="flex items-center justify-between gap-3 rounded-lg border border-border-light p-3"
          >
            <span class="text-sm text-text-secondary">{{ getAgreementStreamLabel(row.stream) }}</span>
            <StatusBadge
              v-if="row.agreement"
              :label="agreementStatusLabel(row.agreement.status)"
              :variant="row.agreement.status === 'Approved' ? 'success' : 'warning'"
            />
            <span v-else class="text-sm text-text-muted">{{ t('project.overviewTab.notCreatedYet') }}</span>
          </div>
        </div>
        <p v-else class="text-sm text-text-muted">
          {{ t('project.overviewTab.noBillableWorkYet') }}
        </p>

        <p v-if="paymentPlanAgreements.length > 0" class="text-xs text-text-muted">
          {{ t('project.overviewTab.paymentPlanNote') }}
        </p>
      </div>
    </Card>

    <Card v-if="stageContext === 'Contract'">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h3 class="text-sm font-semibold text-text-primary">{{ t('project.overviewTab.contractTitle') }}</h3>
          <BaseButton
            v-if="contractQuotation"
            variant="secondary"
            size="sm"
            class="no-print"
            @click="emit('navigate-tab', 'quotation')"
          >
            {{ t('project.overviewTab.viewApprovedQuotation') }}
          </BaseButton>
        </div>
      </template>
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
          <div>
            <p class="text-xs text-text-muted">{{ t('project.overviewTab.quotationNumber') }}</p>
            <p class="text-sm font-medium text-text-primary">{{ contractQuotation?.quotationNo ?? '—' }}</p>
          </div>
          <div>
            <p class="text-xs text-text-muted">{{ t('project.overviewTab.quotationDate') }}</p>
            <p class="text-sm font-medium text-text-primary">{{ contractQuotation ? formatDate(contractQuotation.issueDate) : '—' }}</p>
          </div>
          <div>
            <p class="text-xs text-text-muted">{{ t('project.overviewTab.quotationAmount') }}</p>
            <p class="text-sm font-medium text-text-primary">{{ contractQuotation ? formatCurrency(contractQuotation.amount) : '—' }}</p>
          </div>
        </div>

        <div class="flex items-center gap-2 rounded-lg border border-warning-100 bg-warning-50 px-3 py-2.5 text-sm text-warning-700">
          <AlertTriangle class="h-4 w-4 shrink-0" />
          <span>{{ t('project.overviewTab.quotationApprovalMustLabel') }}</span>
          <StatusBadge
            v-if="contractQuotation"
            :label="quotationStatusLabel(contractQuotation.status)"
            :variant="contractQuotation.status === 'Approved' ? 'success' : contractQuotation.status === 'Rejected' ? 'danger' : 'neutral'"
          />
          <span v-else class="text-warning-700">{{ t('project.overviewTab.noQuotationLinked') }}</span>
        </div>
      </div>
    </Card>

    <Card v-if="stageContext === 'Design'">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h3 class="text-sm font-semibold text-text-primary">{{ t('project.overviewTab.designTitle') }}</h3>
          <BaseButton variant="secondary" size="sm" class="no-print" @click="emit('navigate-tab', 'design')">{{ t('project.overviewTab.goToDocuments') }}</BaseButton>
        </div>
      </template>
      <div class="flex flex-col gap-4">
        <div v-if="designDocuments.length > 0" class="flex flex-col gap-2">
          <div
            v-for="document in designDocuments"
            :key="document.id"
            class="flex items-center justify-between gap-3 rounded-lg border border-border-light p-3"
          >
            <span class="truncate text-sm text-text-secondary">{{ document.title }}</span>
            <StatusBadge :label="documentStatusLabel(document.status)" :variant="getDocumentStatusVariant(document.status)" />
          </div>
        </div>
        <p v-else class="text-sm text-text-muted">{{ t('project.overviewTab.noDesignDocumentsYet') }}</p>
      </div>
    </Card>

    <Card v-if="stageContext === 'Supervision'">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h3 class="text-sm font-semibold text-text-primary">{{ t('project.overviewTab.supervisionTitle') }}</h3>
          <BaseButton variant="secondary" size="sm" class="no-print" @click="emit('navigate-tab', 'payment-plan')">{{ t('project.overviewTab.goToPaymentPlan') }}</BaseButton>
        </div>
      </template>
      <div class="flex flex-col gap-4">
        <p class="text-sm text-text-secondary">
          {{ project.supervisionStartDate ? formatDate(project.supervisionStartDate) : t('project.overviewTab.notSet') }} –
          {{ project.supervisionEndDate ? formatDate(project.supervisionEndDate) : t('project.overviewTab.ongoing') }}
        </p>

        <div v-if="project.selectedSupervisionActivities && project.selectedSupervisionActivities.length > 0" class="flex flex-col gap-2">
          <div
            v-for="activity in project.selectedSupervisionActivities"
            :key="activity.activityId"
            class="flex items-center justify-between gap-3 rounded-lg border border-border-light p-3"
          >
            <div class="flex flex-col gap-0.5 truncate">
              <span class="truncate text-sm text-text-secondary">{{ activity.activityName }}</span>
              <span class="text-xs text-text-muted">
                {{ formatDate(activity.startDate) }} – {{ activity.endDate ? formatDate(activity.endDate) : t('project.overviewTab.ongoing') }}
              </span>
            </div>
            <span class="shrink-0 text-sm font-medium text-text-primary">{{ formatCurrency(activity.monthlyRate) }}/mo</span>
          </div>
        </div>
        <p v-else class="text-sm text-text-muted">{{ t('project.overviewTab.noSupervisionActivities') }}</p>

        <p class="text-xs text-text-muted">
          {{ t('project.overviewTab.supervisionBillingNote') }}
        </p>
      </div>
    </Card>

    <Card v-if="stageContext === 'Government Submission'">
      <template #header>
        <h3 class="text-sm font-semibold text-text-primary">{{ t('project.overviewTab.requiredDocumentsTitle') }}</h3>
      </template>
      <div class="flex flex-col gap-4">
        <div v-if="requiredForms.length > 0" class="flex flex-col gap-2">
          <div
            v-for="form in requiredForms"
            :key="form.id"
            class="flex items-center justify-between gap-3 rounded-lg border border-border-light p-3"
          >
            <div class="flex flex-col gap-0.5 truncate">
              <span class="truncate text-sm text-text-secondary">{{ form.title }}</span>
              <span class="text-xs text-text-muted">{{ form.formCode }} &middot; {{ form.category }}</span>
            </div>
            <template v-if="filledDocumentFor(form)">
              <BaseButton variant="ghost" size="sm" class="no-print shrink-0" @click="viewFilledDocument(filledDocumentFor(form)!.id)">
                {{ t('project.overviewTab.viewForm') }}
              </BaseButton>
            </template>
            <BaseButton v-else variant="secondary" size="sm" class="no-print shrink-0" @click="openFillDialog(form)">
              {{ t('project.overviewTab.fillForm') }}
            </BaseButton>
          </div>
        </div>
        <p v-else class="text-sm text-text-muted">
          {{ t('project.overviewTab.noFillableFormsYet') }}
        </p>
      </div>
    </Card>

    <Card v-if="stageContext === 'Government Submission'">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h3 class="text-sm font-semibold text-text-primary">{{ t('project.overviewTab.approvalsPermitsTitle') }}</h3>
          <BaseButton variant="secondary" size="sm" class="no-print" @click="emit('navigate-tab', 'government')">{{ t('project.overviewTab.goToDocuments') }}</BaseButton>
        </div>
      </template>
      <div class="flex flex-col gap-4">
        <div v-if="governmentSubmissions.length > 0" class="flex flex-col gap-2">
          <div
            v-for="submission in governmentSubmissions"
            :key="submission.id"
            class="flex items-center justify-between gap-3 rounded-lg border border-border-light p-3"
          >
            <div class="flex flex-col gap-0.5 truncate">
              <span class="truncate text-sm text-text-secondary">
                {{ governmentSubmissionStore.getFormById(submission.formId)?.title ?? submission.submissionNo }}
              </span>
              <span class="text-xs text-text-muted">
                {{ governmentSubmissionStore.getAuthorityById(submission.authorityId)?.name ?? '—' }}
                &middot; {{ t('project.overviewTab.lastWorkedOn', { date: lastWorkedOnDate(submission) ? formatDate(lastWorkedOnDate(submission)!) : '—' }) }}
              </span>
            </div>
            <StatusBadge :label="submissionStatusLabel(submission.status)" :variant="getSubmissionStatusVariant(submission.status)" />
          </div>
        </div>
        <p v-else class="text-sm text-text-muted">{{ t('project.overviewTab.noApprovalsFiledYet') }}</p>
      </div>
    </Card>

    <div v-if="showScopeAndDetails" class="grid grid-cols-1 gap-6 laptop:grid-cols-2">
      <DetailPanel :title="t('project.overviewTab.projectDetailsTitle')" :items="projectDetailItems" />
      <div class="flex flex-col gap-3">
        <DetailPanel :title="t('project.overviewTab.clientDetailsTitle')" :items="clientDetailItems" />
        <div class="flex gap-2 no-print">
          <BaseButton
            v-if="client"
            variant="secondary"
            size="sm"
            :icon="MessageSquare"
            @click="router.push({ name: ROUTE_NAMES.MESSAGE_CENTRE, query: { clientId: client.id } })"
          >
            {{ t('project.overviewTab.messageClient') }}
          </BaseButton>
          <BaseButton
            v-if="client"
            variant="ghost"
            size="sm"
            @click="router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId: client.id } })"
          >
            {{ t('project.overviewTab.viewFullProfile') }}
          </BaseButton>
        </div>
      </div>
    </div>

    <FillGovernmentFormDialog
      v-model="isFillDialogOpen"
      :project-id="project.id"
      :forms="fillDialogForm ? [fillDialogForm] : []"
    />
  </div>
</template>
