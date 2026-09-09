<script setup lang="ts">
import { AlertTriangle, CheckCircle2, Mail, MessageSquare } from '@lucide/vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import AddLinkDocumentDialog from '@/components/document/AddLinkDocumentDialog.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import DetailPanel from '@/components/common/DetailPanel.vue'
import SignedDocumentUploadDialog from '@/components/common/SignedDocumentUploadDialog.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextArea from '@/components/common/TextArea.vue'
import DocumentPreviewDialog from '@/components/document/DocumentPreviewDialog.vue'
import FillGovernmentFormDialog from '@/components/government/FillGovernmentFormDialog.vue'
import AgreementFormDialog from '@/components/payment/AgreementFormDialog.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useClientStore } from '@/stores/clientStore'
import { useContractStore } from '@/stores/contractStore'
import { useDocumentStore } from '@/stores/documentStore'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { usePaymentStore } from '@/stores/paymentStore'
import { useProjectLinkDocumentStore } from '@/stores/projectLinkDocumentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useToastStore } from '@/stores/toastStore'
import { documentRequirementService } from '@/services/documentRequirementService'
import { projectService } from '@/services/projectService'
import type { DocumentRequirementLink, DocumentRequirementTargetType } from '@/types/DocumentRequirement'
import type { AgreementStream, CreateAgreementInput } from '@/types/Payment'
import type { Client } from '@/types/Client'
import type { GovernmentForm } from '@/types/Government'
import type { HandoverStatus, Project, ProjectWorkspaceTabKey, WorkflowStage } from '@/types/Project'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate, formatDateTime } from '@/utils/dateFormatter'
import { getClientVerificationVariant } from '@/utils/clientHelpers'
import { getDocumentStatusVariant } from '@/utils/documentHelpers'
import { formMatchesProjectService } from '@/utils/governmentFormHelpers'
import { getAgreementStreamLabel } from '@/utils/paymentHelpers'
import { getSubmissionStatusVariant } from '@/utils/submissionHelpers'
import { getSelectedActivityStatusVariant, getSelectedPermitStatusVariant, getWorkflowStageLabel } from '@/utils/projectHelpers'

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
const projectStore = useProjectStore()
const linkDocumentStore = useProjectLinkDocumentStore()
const toastStore = useToastStore()
const { t } = useI18n()

// "For all service completions either there should be a document link
// uploaded or click check boxes in right to override" -- marking a
// Design activity/Permit/Supervision activity Complete is gated on this
// project having at least one Project Closure document link on file
// (reusing the existing link-document system as-is, see
// AddLinkDocumentDialog.vue/projectLinkDocumentStore.ts) or the
// specific row's own override checkbox. Project-scoped, not per-item --
// there's no field linking a ProjectLinkDocument to the exact item it's
// evidence for (see project_service._assert_completion_evidence on the
// backend, which enforces the same rule for real). overrides is keyed
// by "design:<id>" / "permit:<id>" / "supervision:<id>" so all three
// item kinds share one reactive map without their id spaces colliding.
type CompletionKind = 'design' | 'permit' | 'supervision'
const overrides = reactive<Record<string, boolean>>({})
function overrideKey(kind: CompletionKind, id: string): string {
  return `${kind}:${id}`
}
const hasProjectClosureDocument = computed(
  () => linkDocumentStore.documentsForCategory(props.project.id, 'Project Closure').length > 0,
)
function canMarkComplete(kind: CompletionKind, id: string): boolean {
  return hasProjectClosureDocument.value || Boolean(overrides[overrideKey(kind, id)])
}
function setOverride(kind: CompletionKind, id: string, checked: boolean): void {
  overrides[overrideKey(kind, id)] = checked
}

const isAddClosureDocDialogOpen = ref(false)
function openAddClosureDocDialog(): void {
  isAddClosureDocDialogOpen.value = true
}

onMounted(() => linkDocumentStore.loadForProject(props.project.id))
watch(() => props.project.id, (projectId) => linkDocumentStore.loadForProject(projectId))

// Guards each row's own Close/Reopen buttons individually so acting on
// one activity doesn't disable the others while its request is in
// flight.
const activityActionPendingId = ref<string>()

async function closeDesignActivity(activityId: string, status: 'Complete' | 'Cancelled'): Promise<void> {
  activityActionPendingId.value = activityId
  try {
    await projectService.closeDesignActivity(props.project.id, activityId, status, overrides[overrideKey('design', activityId)])
    await projectStore.refreshProject(props.project.id)
    await loadHandoverStatus()
    toastStore.show('success', t('project.overviewTab.activityClosed'))
  } catch (error) {
    toastStore.show('error', t('project.overviewTab.failedToCloseActivity'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    activityActionPendingId.value = undefined
  }
}

async function reopenDesignActivity(activityId: string): Promise<void> {
  activityActionPendingId.value = activityId
  try {
    await projectService.reopenDesignActivity(props.project.id, activityId)
    await projectStore.refreshProject(props.project.id)
    toastStore.show('success', t('project.overviewTab.activityReopened'))
  } catch (error) {
    toastStore.show('error', t('project.overviewTab.failedToReopenActivity'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    activityActionPendingId.value = undefined
  }
}

// The user always sets a Permit's status directly, at their own
// discretion (see project_service.set_permit_status) -- on top of the
// auto-close that happens once every task linked to it (see the Tasks
// tab) is completed.
const permitActionPendingId = ref<string>()

async function setPermitStatus(permitId: string, status: 'In Progress' | 'Complete' | 'Cancelled'): Promise<void> {
  permitActionPendingId.value = permitId
  try {
    await projectService.setPermitStatus(props.project.id, permitId, status, overrides[overrideKey('permit', permitId)])
    await projectStore.refreshProject(props.project.id)
    await loadHandoverStatus()
    toastStore.show('success', t('project.overviewTab.activityClosed'))
  } catch (error) {
    toastStore.show('error', t('project.overviewTab.failedToCloseActivity'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    permitActionPendingId.value = undefined
  }
}

// Same direct-status pattern as Permits, based on the user's own read
// of site-engineer reports, on top of the same task-driven auto-close.
const supervisionActionPendingId = ref<string>()

async function setSupervisionStatus(activityId: string, status: 'In Progress' | 'Complete' | 'Cancelled'): Promise<void> {
  supervisionActionPendingId.value = activityId
  try {
    await projectService.setSupervisionStatus(props.project.id, activityId, status, overrides[overrideKey('supervision', activityId)])
    await projectStore.refreshProject(props.project.id)
    await loadHandoverStatus()
    toastStore.show('success', t('project.overviewTab.activityClosed'))
  } catch (error) {
    toastStore.show('error', t('project.overviewTab.failedToCloseActivity'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    supervisionActionPendingId.value = undefined
  }
}

// Hand-over: populated (checklist non-empty) once every planned Design/
// Permit/Supervision item is closed and payment is fully settled (see
// project_service.try_complete_project) -- independent of stageContext
// since it can become true while viewing any stage's tab, so it's
// loaded unconditionally rather than gated by loadStageDataIfNeeded.
const handoverStatus = ref<HandoverStatus>()

async function loadHandoverStatus(): Promise<void> {
  try {
    handoverStatus.value = await projectService.getHandoverStatus(props.project.id)
  } catch {
    handoverStatus.value = undefined
  }
}

const showHandoverCard = computed(() => props.project.status === 'Completed' || (handoverStatus.value?.checklist.length ?? 0) > 0)

const isHandoverDialogOpen = ref(false)
const isHandoverSaving = ref(false)

async function handleConfirmHandover(payload: { file: File }): Promise<void> {
  isHandoverSaving.value = true
  try {
    await projectService.confirmProjectHandover(props.project.id, payload.file)
    await projectStore.refreshProject(props.project.id)
    await loadHandoverStatus()
    isHandoverDialogOpen.value = false
    toastStore.show('success', t('project.overviewTab.handover.confirmedTitle'), t('project.overviewTab.handover.confirmedDescription'))
  } catch (error) {
    toastStore.show('error', t('project.overviewTab.handover.failedToConfirm'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isHandoverSaving.value = false
  }
}

// Read-only reference checklist ("what documents are typically needed
// for this") on each Design/Permit/Supervision row -- admin-defined,
// informational only, never blocks closing anything. Fetched lazily,
// per row, only once expanded -- same pattern as the admin catalog
// panels' own prerequisites/links disclosures. Keyed by
// "targetType:targetCatalogId" since all three tracks share this one
// disclosure state.
const expandedReferenceDocsKey = ref<string>()
const referenceDocsByKey = reactive<Record<string, DocumentRequirementLink[]>>({})
const isLoadingReferenceDocs = ref<string>()

async function toggleReferenceDocs(targetType: DocumentRequirementTargetType, targetCatalogId: string): Promise<void> {
  const key = `${targetType}:${targetCatalogId}`
  if (expandedReferenceDocsKey.value === key) {
    expandedReferenceDocsKey.value = undefined
    return
  }
  expandedReferenceDocsKey.value = key
  if (referenceDocsByKey[key]) return
  isLoadingReferenceDocs.value = key
  try {
    referenceDocsByKey[key] = await documentRequirementService.getLinksForTarget(targetType, targetCatalogId)
  } catch {
    referenceDocsByKey[key] = []
  } finally {
    isLoadingReferenceDocs.value = undefined
  }
}

// Scope is only useful while the project is still being set up -- once
// it's past Quotation, staff are working from that stage's own overview
// card instead, and repeating this same block on every stage's Overview
// was reported as noise.
const showScope = computed(() => props.stageContext === 'Requirement' || props.stageContext === 'Quotation')

// Project Details / Client Details / Message Client / View Full Profile
// are Quotation-stage-only now -- the Requirement/Scope stage's Overview
// was simplified down to just the Scope card itself plus its own Edit /
// Save & Proceed controls, dropping everything else that used to repeat
// here (reported as clutter on a page whose only real job at this stage
// is finalizing and confirming the scope).
const showProjectAndClientDetails = computed(() => props.stageContext === 'Quotation')

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
    (props.project.selectedSupervisionActivities && props.project.selectedSupervisionActivities.length > 0) ||
    (props.project.selectedPermits && props.project.selectedPermits.length > 0),
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

onMounted(loadHandoverStatus)
watch(() => props.project.id, loadHandoverStatus)

// Civil ID is filed under the 'Identity Document' category regardless of
// the client's actual document-type label -- see
// getDocumentCategoryForIdentificationType (constants/clientOptions.ts).
const civilIdDocument = computed(() => clientStore.documents.find((document) => document.category === 'Identity Document'))

// Mirrors the backend's real Requirement -> Quotation exit criterion
// exactly (project_service._assert_stage_exit_criteria) -- a
// ClientIdentification record on file, not just any uploaded document.
const hasClientIdentification = computed(() => clientStore.identifications.length > 0)

// Same check the backend's exit criterion makes (project.description
// non-empty) -- deliberately not the broader hasScope (which also goes
// true off selectedActivities/selectedSupervisionActivities alone), so
// this can never show Save & Proceed enabled in a state the server
// would still reject.
const hasScopeText = computed(() => Boolean((props.project.description ?? '').trim()))
const canAdvanceToQuotation = computed(
  () => hasScopeText.value && hasClientIdentification.value && !props.project.scopeClientConfirmedAt,
)

// Once a quotation has actually been Approved, the scope it was built
// against is frozen -- same rule as the backend's own gate
// (project_service._assert_requirement_editable), and the only condition
// under which Edit/Save & Proceed disappear. quotationStore.quotations is
// already loaded unconditionally by ProjectWorkspacePage.vue before any
// tab (this one included) mounts, so no extra fetch is needed here.
const isScopeLocked = computed(() => quotationStore.quotations.some((quotation) => quotation.status === 'Approved'))

// Scope of Work used to be edited on a separate Requirement tab (Save
// Scope + a distinct Confirm action, plus its own Project/Client Details
// cards) -- collapsed into this one Scope card instead: an inline Edit
// toggle swaps the read-only description for a draft textarea, and a
// single Save & Proceed both persists any edit and confirms/advances,
// removing the separate save-only step.
const isEditingScope = ref(false)
const scopeDraft = ref('')

function startEditingScope(): void {
  scopeDraft.value = props.project.description ?? ''
  isEditingScope.value = true
}

const isAdvancingToQuotation = ref(false)

// Gated on canAdvanceToQuotation so it can only ever fire once:
// confirming sets project.scopeClientConfirmedAt, which immediately
// flips that guard false on the refreshed project.
//
// Navigates to 'quotation' on success rather than just refreshing in
// place -- stageContext (what this whole Overview tab renders)
// deliberately does NOT follow project.currentStage on an ordinary
// refreshProject() call (see ProjectWorkspacePage.vue's own comment on
// that watcher, there to stop an unrelated background update from
// yanking someone's stepper-driven view out from under them); only an
// explicit navigate-tab updates it. Without this, staff would advance
// the project but keep looking at a stale Requirement-stage Overview.
async function handleSaveAndProceed(): Promise<void> {
  isAdvancingToQuotation.value = true
  try {
    const draft = scopeDraft.value.trim()
    if (isEditingScope.value && draft && draft !== (props.project.description ?? '').trim()) {
      await projectService.saveScopeOfWork(props.project.id, draft, undefined, undefined)
    }
    await projectService.confirmRequirementScope(props.project.id)
    await projectStore.refreshProject(props.project.id)
    isEditingScope.value = false
    toastStore.show('success', t('project.overviewTab.scopeConfirmedTitle'), t('project.overviewTab.scopeConfirmedDescription'))
    emit('navigate-tab', 'quotation')
  } catch (error) {
    toastStore.show(
      'error',
      t('project.overviewTab.failedToSaveScope'),
      error instanceof Error ? error.message : t('common.pleaseTryAgain'),
    )
  } finally {
    isAdvancingToQuotation.value = false
  }
}

function viewCivilIdDocument(): void {
  if (!props.client || !civilIdDocument.value) return
  clientStore.viewDocument(props.client.id, civilIdDocument.value.id).catch(() => {
    toastStore.show('error', t('project.documentsTab.failedToOpenDocument'), t('common.pleaseTryAgain'))
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

// Whichever visible stream doesn't have a plan yet -- undefined once
// every one does, at which point there's nothing left to create here
// and the header action goes back to just opening the full tab.
const nextMissingPaymentPlanStream = computed(() => paymentPlanAgreements.value.find((row) => !row.agreement)?.stream)

const isPaymentPlanFormOpen = ref(false)
const paymentPlanFormStream = ref<AgreementStream>('Design')

function openCreatePaymentPlan(): void {
  if (!nextMissingPaymentPlanStream.value) return
  paymentPlanFormStream.value = nextMissingPaymentPlanStream.value
  isPaymentPlanFormOpen.value = true
}

// Creates the agreement right here instead of sending staff to the
// Payment Plan tab just to open the same dialog -- paymentPlanAgreements
// above reads straight from paymentStore.agreements, so the result
// (the newly created Draft plan) shows in this card immediately once
// createAgreement resolves, no extra fetch needed.
async function handleSubmitPaymentPlan(input: CreateAgreementInput): Promise<void> {
  try {
    const agreement = await paymentStore.createAgreement(input, 'Rajan Kumar')
    toastStore.show('success', t('project.overviewTab.paymentPlanCreatedTitle'), t('project.overviewTab.paymentPlanCreatedDescription', { stream: getAgreementStreamLabel(agreement.stream) }))
    isPaymentPlanFormOpen.value = false
  } catch (error) {
    toastStore.show('error', t('project.overviewTab.failedToCreatePaymentPlan'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  }
}

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

// Opens the filled document inline, without leaving the project
// workspace -- this used to route to the standalone /documents/:id
// page, which dropped the user out of the project entirely.
const isPreviewOpen = ref(false)
const previewDocumentId = ref<string | undefined>(undefined)

function viewFilledDocument(documentId: string): void {
  previewDocumentId.value = documentId
  isPreviewOpen.value = true
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
  <div class="flex flex-col gap-3">
    <Card v-if="showHandoverCard">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h3 class="text-sm font-semibold text-text-primary">{{ t('project.overviewTab.handover.title') }}</h3>
          <StatusBadge
            v-if="project.status === 'Completed'"
            :label="t('project.overviewTab.handover.acknowledged')"
            variant="success"
          />
          <StatusBadge
            v-else
            :label="t('project.overviewTab.handover.awaitingAcknowledgment')"
            variant="warning"
          />
        </div>
      </template>

      <ul v-if="handoverStatus?.checklist.length" class="flex flex-col gap-1.5">
        <li
          v-for="item in handoverStatus.checklist"
          :key="item.id"
          class="flex items-center gap-2 text-sm text-text-secondary"
        >
          <CheckCircle2 class="h-4 w-4 shrink-0 text-status-success" />
          <span>{{ item.title }}</span>
          <span class="text-xs text-text-muted">({{ item.sourceType }})</span>
        </li>
      </ul>

      <div class="mt-3 flex flex-wrap items-center justify-between gap-3 border-t border-border-light pt-3">
        <p v-if="project.status === 'Completed' && handoverStatus?.handoverAcknowledgedAt" class="text-sm text-text-secondary">
          {{ t('project.overviewTab.handover.acknowledgedOnFragment', { date: formatDateTime(handoverStatus.handoverAcknowledgedAt) }) }}
        </p>
        <p v-else-if="handoverStatus?.handoverSentAt" class="text-sm text-text-secondary">
          {{ t('project.overviewTab.handover.readySinceFragment', { date: formatDateTime(handoverStatus.handoverSentAt) }) }}
        </p>
        <p v-else class="text-sm text-text-secondary">{{ t('project.overviewTab.handover.readyToSend') }}</p>

        <BaseButton
          v-if="project.status !== 'Completed' && client"
          size="sm"
          :icon="Mail"
          :loading="isHandoverSaving"
          class="no-print"
          @click="isHandoverDialogOpen = true"
        >
          {{ t('project.overviewTab.handover.confirmHandover') }}
        </BaseButton>
      </div>

      <SignedDocumentUploadDialog
        v-if="client"
        v-model="isHandoverDialogOpen"
        :loading="isHandoverSaving"
        :title="t('project.overviewTab.handover.confirmDialogTitle')"
        :description="t('project.overviewTab.handover.confirmDialogDescription')"
        @confirm="handleConfirmHandover"
      />
    </Card>

    <Card v-if="hasScope && showScope">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <h3 class="text-sm font-semibold text-text-primary">{{ t('project.overviewTab.scopeTitle') }}</h3>
          <BaseButton
            v-if="stageContext === 'Requirement' && !isScopeLocked && !isEditingScope"
            variant="ghost" size="sm" class="no-print"
            @click="startEditingScope"
          >
            {{ t('project.overviewTab.editScope') }}
          </BaseButton>
        </div>
      </template>

      <TextArea
        v-if="isEditingScope"
        v-model="scopeDraft"
        :rows="6"
      />
      <p v-else-if="project.description" class="whitespace-pre-wrap text-sm text-text-secondary">{{ project.description }}</p>

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
            <span>{{ item.activityName }} ({{ formatDate(item.startDate) }} – {{ formatDate(item.endDate) }})</span>
            <span class="shrink-0 text-text-muted">{{ formatCurrency(item.monthlyRate) }}/mo</span>
          </li>
        </ul>
      </div>

      <div v-if="project.selectedPermits && project.selectedPermits.length > 0" class="mt-3 border-t border-border-light pt-3">
        <p class="mb-1.5 text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.overviewTab.permitsTitle') }}</p>
        <ul class="flex flex-col gap-1">
          <li
            v-for="permit in project.selectedPermits"
            :key="permit.id"
            class="flex items-center justify-between gap-3 text-sm text-text-secondary"
          >
            <span>{{ permit.permitName }}</span>
            <span class="shrink-0 text-text-muted">{{ permit.permitPrice != null ? formatCurrency(permit.permitPrice) : '—' }}</span>
          </li>
        </ul>
      </div>

      <template v-if="stageContext === 'Requirement' && !isScopeLocked">
        <div v-if="!hasScopeText" class="mt-3 flex items-center gap-2 rounded-lg border border-warning-100 bg-warning-50 px-3 py-2.5 text-sm text-warning-700">
          <AlertTriangle class="h-4 w-4 shrink-0" />
          <span>{{ t('project.overviewTab.noScopeWarning') }}</span>
        </div>
        <div v-if="!hasClientIdentification" class="mt-3 flex items-center gap-2 rounded-lg border border-warning-100 bg-warning-50 px-3 py-2.5 text-sm text-warning-700">
          <AlertTriangle class="h-4 w-4 shrink-0" />
          <span>{{ t('project.overviewTab.noClientIdWarning') }}</span>
        </div>

        <BaseButton
          class="mt-3 no-print"
          :disabled="!canAdvanceToQuotation"
          :loading="isAdvancingToQuotation"
          @click="handleSaveAndProceed"
        >
          {{ t('project.overviewTab.saveAndProceed') }}
        </BaseButton>
      </template>
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
          <BaseButton
            v-if="nextMissingPaymentPlanStream"
            size="sm"
            class="no-print"
            @click="openCreatePaymentPlan"
          >
            {{ t('project.overviewTab.createPaymentPlan') }}
          </BaseButton>
          <BaseButton v-else variant="secondary" size="sm" class="no-print" @click="emit('navigate-tab', 'payment-plan')">
            {{ t('project.overviewTab.goToPaymentPlan') }}
          </BaseButton>
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
        <div class="flex flex-col gap-2">
          <span class="text-xs font-medium text-text-muted">{{ t('project.overviewTab.designActivitiesTitle') }}</span>
          <div v-if="project.selectedActivities && project.selectedActivities.length > 0" class="flex flex-col gap-2">
            <div
              v-for="activity in project.selectedActivities"
              :key="activity.id ?? activity.activityId"
              class="flex flex-col gap-2 rounded-lg border border-border-light p-3"
            >
              <div class="flex flex-wrap items-center justify-between gap-3">
                <span class="truncate text-sm text-text-secondary">{{ activity.activityName }}</span>
                <div class="flex items-center gap-2">
                  <StatusBadge :label="activity.status ?? 'Not Started'" :variant="getSelectedActivityStatusVariant(activity.status ?? 'Not Started')" />
                  <template v-if="activity.id">
                    <template v-if="activity.status === 'Complete' || activity.status === 'Cancelled'">
                      <BaseButton
                        variant="secondary" size="sm" class="no-print"
                        :loading="activityActionPendingId === activity.id"
                        @click="reopenDesignActivity(activity.id)"
                      >{{ t('project.overviewTab.reopenActivity') }}</BaseButton>
                    </template>
                    <template v-else>
                      <BaseButton
                        variant="secondary" size="sm" class="no-print"
                        :loading="activityActionPendingId === activity.id"
                        @click="closeDesignActivity(activity.id, 'Cancelled')"
                      >{{ t('project.overviewTab.markCancelled') }}</BaseButton>
                      <BaseButton
                        variant="primary" size="sm" class="no-print"
                        :loading="activityActionPendingId === activity.id"
                        :disabled="!canMarkComplete('design', activity.id)"
                        @click="closeDesignActivity(activity.id, 'Complete')"
                      >{{ t('project.overviewTab.markComplete') }}</BaseButton>
                      <div v-if="!canMarkComplete('design', activity.id)" class="flex items-center gap-2 text-xs no-print">
                        <label class="inline-flex items-center gap-1.5 text-text-muted">
                          <input
                            type="checkbox"
                            class="h-3.5 w-3.5 rounded border-border-default"
                            :checked="overrides[overrideKey('design', activity.id)]"
                            @change="setOverride('design', activity.id, ($event.target as HTMLInputElement).checked)"
                          />
                          {{ t('project.overviewTab.overrideNoDocument') }}
                        </label>
                        <button type="button" class="font-medium text-primary-600 hover:text-primary-700" @click="openAddClosureDocDialog">
                          {{ t('project.overviewTab.addClosureDocument') }}
                        </button>
                      </div>
                    </template>
                  </template>
                </div>
              </div>
              <button
                type="button"
                class="self-start text-xs font-medium text-primary-600 no-print hover:text-primary-700"
                @click="toggleReferenceDocs('Design', activity.activityId)"
              >{{ t('project.overviewTab.referenceDocuments') }}</button>
              <div v-if="expandedReferenceDocsKey === `Design:${activity.activityId}`" class="flex flex-col gap-1">
                <SkeletonLoader v-if="isLoadingReferenceDocs === `Design:${activity.activityId}`" :rows="1" />
                <p v-else-if="(referenceDocsByKey[`Design:${activity.activityId}`] ?? []).length === 0" class="text-xs text-text-muted">
                  {{ t('project.overviewTab.noReferenceDocuments') }}
                </p>
                <ul v-else class="list-inside list-disc text-xs text-text-muted">
                  <li v-for="link in referenceDocsByKey[`Design:${activity.activityId}`]" :key="link.id">{{ link.requirementName }}</li>
                </ul>
              </div>
            </div>
          </div>
          <p v-else class="text-sm text-text-muted">{{ t('project.overviewTab.noDesignActivitiesYet') }}</p>
        </div>

        <div class="flex flex-col gap-2">
          <span class="text-xs font-medium text-text-muted">{{ t('project.overviewTab.permitsTitle') }}</span>
          <div v-if="project.selectedPermits && project.selectedPermits.length > 0" class="flex flex-col gap-2">
            <div
              v-for="permit in project.selectedPermits"
              :key="permit.id"
              class="flex flex-col gap-2 rounded-lg border border-border-light p-3"
            >
              <div class="flex flex-wrap items-center justify-between gap-3">
                <span class="truncate text-sm text-text-secondary">{{ permit.permitName }}</span>
                <div class="flex items-center gap-2">
                  <StatusBadge :label="permit.status" :variant="getSelectedPermitStatusVariant(permit.status)" />
                  <template v-if="permit.status === 'Complete' || permit.status === 'Cancelled'">
                    <BaseButton
                      variant="secondary" size="sm" class="no-print"
                      :loading="permitActionPendingId === permit.id"
                      @click="setPermitStatus(permit.id, 'In Progress')"
                    >{{ t('project.overviewTab.reopenActivity') }}</BaseButton>
                  </template>
                  <template v-else>
                    <BaseButton
                      v-if="permit.status !== 'In Progress'"
                      variant="secondary" size="sm" class="no-print"
                      :loading="permitActionPendingId === permit.id"
                      @click="setPermitStatus(permit.id, 'In Progress')"
                    >{{ t('project.overviewTab.startApplication') }}</BaseButton>
                    <BaseButton
                      variant="secondary" size="sm" class="no-print"
                      :loading="permitActionPendingId === permit.id"
                      @click="setPermitStatus(permit.id, 'Cancelled')"
                    >{{ t('project.overviewTab.markCancelled') }}</BaseButton>
                    <BaseButton
                      variant="primary" size="sm" class="no-print"
                      :loading="permitActionPendingId === permit.id"
                      :disabled="!canMarkComplete('permit', permit.id)"
                      @click="setPermitStatus(permit.id, 'Complete')"
                    >{{ t('project.overviewTab.markComplete') }}</BaseButton>
                    <div v-if="!canMarkComplete('permit', permit.id)" class="flex items-center gap-2 text-xs no-print">
                      <label class="inline-flex items-center gap-1.5 text-text-muted">
                        <input
                          type="checkbox"
                          class="h-3.5 w-3.5 rounded border-border-default"
                          :checked="overrides[overrideKey('permit', permit.id)]"
                          @change="setOverride('permit', permit.id, ($event.target as HTMLInputElement).checked)"
                        />
                        {{ t('project.overviewTab.overrideNoDocument') }}
                      </label>
                      <button type="button" class="font-medium text-primary-600 hover:text-primary-700" @click="openAddClosureDocDialog">
                        {{ t('project.overviewTab.addClosureDocument') }}
                      </button>
                    </div>
                  </template>
                </div>
              </div>
              <button
                v-if="permit.permitId"
                type="button"
                class="self-start text-xs font-medium text-primary-600 no-print hover:text-primary-700"
                @click="toggleReferenceDocs('Permit', permit.permitId)"
              >{{ t('project.overviewTab.referenceDocuments') }}</button>
              <div v-if="permit.permitId && expandedReferenceDocsKey === `Permit:${permit.permitId}`" class="flex flex-col gap-1">
                <SkeletonLoader v-if="isLoadingReferenceDocs === `Permit:${permit.permitId}`" :rows="1" />
                <p v-else-if="(referenceDocsByKey[`Permit:${permit.permitId}`] ?? []).length === 0" class="text-xs text-text-muted">
                  {{ t('project.overviewTab.noReferenceDocuments') }}
                </p>
                <ul v-else class="list-inside list-disc text-xs text-text-muted">
                  <li v-for="link in referenceDocsByKey[`Permit:${permit.permitId}`]" :key="link.id">{{ link.requirementName }}</li>
                </ul>
              </div>
            </div>
          </div>
          <p v-else class="text-sm text-text-muted">{{ t('project.overviewTab.noPermitsSelectedYet') }}</p>
        </div>

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
            class="flex flex-col gap-2 rounded-lg border border-border-light p-3"
          >
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div class="flex flex-col gap-0.5 truncate">
                <span class="truncate text-sm text-text-secondary">{{ activity.activityName }}</span>
                <span class="text-xs text-text-muted">
                  {{ formatDate(activity.startDate) }} – {{ formatDate(activity.endDate) }}
                </span>
              </div>
              <div class="flex items-center gap-2">
                <span class="shrink-0 text-sm font-medium text-text-primary">{{ formatCurrency(activity.monthlyRate) }}/mo</span>
                <StatusBadge v-if="activity.status" :label="activity.status" :variant="getSelectedPermitStatusVariant(activity.status)" />
                <template v-if="activity.id">
                  <template v-if="activity.status === 'Complete' || activity.status === 'Cancelled'">
                    <BaseButton
                      variant="secondary" size="sm" class="no-print"
                      :loading="supervisionActionPendingId === activity.id"
                      @click="setSupervisionStatus(activity.id, 'In Progress')"
                    >{{ t('project.overviewTab.reopenActivity') }}</BaseButton>
                  </template>
                  <template v-else>
                    <BaseButton
                      v-if="activity.status !== 'In Progress'"
                      variant="secondary" size="sm" class="no-print"
                      :loading="supervisionActionPendingId === activity.id"
                      @click="setSupervisionStatus(activity.id, 'In Progress')"
                    >{{ t('project.overviewTab.startApplication') }}</BaseButton>
                    <BaseButton
                      variant="secondary" size="sm" class="no-print"
                      :loading="supervisionActionPendingId === activity.id"
                      @click="setSupervisionStatus(activity.id, 'Cancelled')"
                    >{{ t('project.overviewTab.markCancelled') }}</BaseButton>
                    <BaseButton
                      variant="primary" size="sm" class="no-print"
                      :loading="supervisionActionPendingId === activity.id"
                      :disabled="!canMarkComplete('supervision', activity.id)"
                      @click="setSupervisionStatus(activity.id, 'Complete')"
                    >{{ t('project.overviewTab.markComplete') }}</BaseButton>
                    <div v-if="!canMarkComplete('supervision', activity.id)" class="flex items-center gap-2 text-xs no-print">
                      <label class="inline-flex items-center gap-1.5 text-text-muted">
                        <input
                          type="checkbox"
                          class="h-3.5 w-3.5 rounded border-border-default"
                          :checked="overrides[overrideKey('supervision', activity.id)]"
                          @change="setOverride('supervision', activity.id, ($event.target as HTMLInputElement).checked)"
                        />
                        {{ t('project.overviewTab.overrideNoDocument') }}
                      </label>
                      <button type="button" class="font-medium text-primary-600 hover:text-primary-700" @click="openAddClosureDocDialog">
                        {{ t('project.overviewTab.addClosureDocument') }}
                      </button>
                    </div>
                  </template>
                </template>
              </div>
            </div>
            <button
              type="button"
              class="self-start text-xs font-medium text-primary-600 no-print hover:text-primary-700"
              @click="toggleReferenceDocs('Supervision', activity.activityId)"
            >{{ t('project.overviewTab.referenceDocuments') }}</button>
            <div v-if="expandedReferenceDocsKey === `Supervision:${activity.activityId}`" class="flex flex-col gap-1">
              <SkeletonLoader v-if="isLoadingReferenceDocs === `Supervision:${activity.activityId}`" :rows="1" />
              <p v-else-if="(referenceDocsByKey[`Supervision:${activity.activityId}`] ?? []).length === 0" class="text-xs text-text-muted">
                {{ t('project.overviewTab.noReferenceDocuments') }}
              </p>
              <ul v-else class="list-inside list-disc text-xs text-text-muted">
                <li v-for="link in referenceDocsByKey[`Supervision:${activity.activityId}`]" :key="link.id">{{ link.requirementName }}</li>
              </ul>
            </div>
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
        <div class="flex flex-col gap-2">
          <span class="text-xs font-medium text-text-muted">{{ t('project.overviewTab.permitsTitle') }}</span>
          <div v-if="project.selectedPermits && project.selectedPermits.length > 0" class="flex flex-col gap-2">
            <div
              v-for="permit in project.selectedPermits"
              :key="permit.id"
              class="flex flex-col gap-2 rounded-lg border border-border-light p-3"
            >
              <div class="flex flex-wrap items-center justify-between gap-3">
                <span class="truncate text-sm text-text-secondary">{{ permit.permitName }}</span>
                <div class="flex items-center gap-2">
                  <StatusBadge :label="permit.status" :variant="getSelectedPermitStatusVariant(permit.status)" />
                  <template v-if="permit.status === 'Complete' || permit.status === 'Cancelled'">
                    <BaseButton
                      variant="secondary" size="sm" class="no-print"
                      :loading="permitActionPendingId === permit.id"
                      @click="setPermitStatus(permit.id, 'In Progress')"
                    >{{ t('project.overviewTab.reopenActivity') }}</BaseButton>
                  </template>
                  <template v-else>
                    <BaseButton
                      v-if="permit.status !== 'In Progress'"
                      variant="secondary" size="sm" class="no-print"
                      :loading="permitActionPendingId === permit.id"
                      @click="setPermitStatus(permit.id, 'In Progress')"
                    >{{ t('project.overviewTab.startApplication') }}</BaseButton>
                    <BaseButton
                      variant="secondary" size="sm" class="no-print"
                      :loading="permitActionPendingId === permit.id"
                      @click="setPermitStatus(permit.id, 'Cancelled')"
                    >{{ t('project.overviewTab.markCancelled') }}</BaseButton>
                    <BaseButton
                      variant="primary" size="sm" class="no-print"
                      :loading="permitActionPendingId === permit.id"
                      :disabled="!canMarkComplete('permit', permit.id)"
                      @click="setPermitStatus(permit.id, 'Complete')"
                    >{{ t('project.overviewTab.markComplete') }}</BaseButton>
                    <div v-if="!canMarkComplete('permit', permit.id)" class="flex items-center gap-2 text-xs no-print">
                      <label class="inline-flex items-center gap-1.5 text-text-muted">
                        <input
                          type="checkbox"
                          class="h-3.5 w-3.5 rounded border-border-default"
                          :checked="overrides[overrideKey('permit', permit.id)]"
                          @change="setOverride('permit', permit.id, ($event.target as HTMLInputElement).checked)"
                        />
                        {{ t('project.overviewTab.overrideNoDocument') }}
                      </label>
                      <button type="button" class="font-medium text-primary-600 hover:text-primary-700" @click="openAddClosureDocDialog">
                        {{ t('project.overviewTab.addClosureDocument') }}
                      </button>
                    </div>
                  </template>
                </div>
              </div>
              <button
                v-if="permit.permitId"
                type="button"
                class="self-start text-xs font-medium text-primary-600 no-print hover:text-primary-700"
                @click="toggleReferenceDocs('Permit', permit.permitId)"
              >{{ t('project.overviewTab.referenceDocuments') }}</button>
              <div v-if="permit.permitId && expandedReferenceDocsKey === `Permit:${permit.permitId}`" class="flex flex-col gap-1">
                <SkeletonLoader v-if="isLoadingReferenceDocs === `Permit:${permit.permitId}`" :rows="1" />
                <p v-else-if="(referenceDocsByKey[`Permit:${permit.permitId}`] ?? []).length === 0" class="text-xs text-text-muted">
                  {{ t('project.overviewTab.noReferenceDocuments') }}
                </p>
                <ul v-else class="list-inside list-disc text-xs text-text-muted">
                  <li v-for="link in referenceDocsByKey[`Permit:${permit.permitId}`]" :key="link.id">{{ link.requirementName }}</li>
                </ul>
              </div>
            </div>
          </div>
          <p v-else class="text-sm text-text-muted">{{ t('project.overviewTab.noPermitsSelectedYet') }}</p>
        </div>

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

    <div v-if="showProjectAndClientDetails" class="grid grid-cols-1 gap-6 laptop:grid-cols-2">
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
    <DocumentPreviewDialog v-model="isPreviewOpen" :document-id="previewDocumentId" />
    <AgreementFormDialog
      v-model="isPaymentPlanFormOpen"
      :project-id="project.id"
      :stream="paymentPlanFormStream"
      mode="create"
      :existing-obligations="[]"
      :approved-contract="
        paymentPlanQuotation
          ? { quotationNo: paymentPlanQuotation.quotationNo, contractValue: paymentPlanQuotation.amount, currency: paymentPlanQuotation.currency }
          : undefined
      "
      :is-submitting="paymentStore.isSubmitting"
      @submit="handleSubmitPaymentPlan"
    />
    <AddLinkDocumentDialog
      v-model="isAddClosureDocDialogOpen"
      :project-id="project.id"
      category="Project Closure"
    />
  </div>
</template>
