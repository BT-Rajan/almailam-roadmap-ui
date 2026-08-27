<script setup lang="ts">
import { AlertTriangle, MessageSquare } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
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
import { useQuotationStore } from '@/stores/quotationStore'
import { useToastStore } from '@/stores/toastStore'
import type { Client } from '@/types/Client'
import type { GovernmentForm } from '@/types/Government'
import type { Project, ProjectWorkspaceTabKey, WorkflowStage } from '@/types/Project'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { getClientVerificationVariant } from '@/utils/clientHelpers'
import { getDocumentStatusVariant } from '@/utils/documentHelpers'
import { formMatchesProjectService } from '@/utils/governmentFormHelpers'
import { getSubmissionStatusVariant } from '@/utils/submissionHelpers'
import { getWorkflowStageLabel } from '@/utils/projectHelpers'

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
const contractStore = useContractStore()
const documentStore = useDocumentStore()
const governmentSubmissionStore = useGovernmentSubmissionStore()
const toastStore = useToastStore()

// Scope, Project Details, and Client Details are only useful while the
// project is still being set up -- once it's past Quotation, staff are
// working from that stage's own overview card instead, and repeating this
// same block on every stage's Overview was reported as noise.
const showScopeAndDetails = computed(() => props.stageContext === 'Requirement' || props.stageContext === 'Quotation')

const projectDetailItems = computed(() => [
  { label: 'Service', value: props.project.service },
  { label: 'Field Engineer', value: props.project.engineer },
  { label: 'Start Date', value: formatDate(props.project.startDate) },
  { label: 'Target Completion Date', value: formatDate(props.project.targetDate) },
  { label: 'Current Stage', value: getWorkflowStageLabel(props.project.currentStage) },
  { label: 'Priority', value: props.project.priority },
])

const clientDetailItems = computed(() => {
  if (!props.client) return []
  return [
    { label: 'Company Name', value: props.client.companyName },
    { label: 'Contact Person', value: props.client.contactPerson },
    { label: 'Mobile', value: props.client.mobile },
    { label: 'Email', value: props.client.email },
    { label: 'City', value: props.client.city },
  ]
})

const hasScope = computed(
  () =>
    Boolean(props.project.description) ||
    (props.project.selectedActivities && props.project.selectedActivities.length > 0) ||
    (props.project.selectedTypeActivities && props.project.selectedTypeActivities.length > 0),
)

// Civil ID verification (Quotation), design document status (Design), and
// the approvals/permits checklist (Government Submission) all need data
// that isn't loaded anywhere else in the project workspace by default --
// fetched only when their card is actually showing, not on every visit to
// this tab regardless of stage context.
function loadStageDataIfNeeded(): void {
  if (props.stageContext === 'Quotation' && props.client) {
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

function viewCivilIdDocument(): void {
  if (!props.client || !civilIdDocument.value) return
  clientStore.viewDocument(props.client.id, civilIdDocument.value.id).catch(() => {
    toastStore.show('error', 'Failed to open document', 'Please try again.')
  })
}

const latestQuotation = computed(() => quotationStore.latestQuotation)

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
</script>

<template>
  <div class="flex flex-col gap-6">
    <Card v-if="hasScope && showScopeAndDetails">
      <template #header>
        <h3 class="text-sm font-semibold text-text-primary">Scope</h3>
      </template>
      <p v-if="project.description" class="whitespace-pre-wrap text-sm text-text-secondary">{{ project.description }}</p>

      <div v-if="project.selectedActivities && project.selectedActivities.length > 0" class="mt-3 border-t border-border-light pt-3">
        <p class="mb-1.5 text-xs font-medium uppercase tracking-wide text-text-muted">Services</p>
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

      <div v-if="project.selectedTypeActivities && project.selectedTypeActivities.length > 0" class="mt-3 border-t border-border-light pt-3">
        <p class="mb-1.5 text-xs font-medium uppercase tracking-wide text-text-muted">Additional Services</p>
        <ul class="flex flex-col gap-1">
          <li
            v-for="item in project.selectedTypeActivities"
            :key="item.id"
            class="flex items-center justify-between gap-3 text-sm text-text-secondary"
          >
            <span>{{ item.activityName }}</span>
            <span class="shrink-0 text-text-muted">{{ item.isCoveredByService ? 'Covered by service' : formatCurrency(item.cost) }}</span>
          </li>
        </ul>
      </div>
    </Card>

    <Card v-if="stageContext === 'Quotation'">
      <template #header>
        <h3 class="text-sm font-semibold text-text-primary">Quotation</h3>
      </template>
      <div class="flex flex-col gap-4">
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm text-text-secondary">Quotation Status</span>
          <StatusBadge
            v-if="latestQuotation"
            :label="latestQuotation.status"
            :variant="latestQuotation.status === 'Approved' ? 'success' : latestQuotation.status === 'Rejected' ? 'danger' : 'neutral'"
          />
          <span v-else class="text-sm text-text-muted">No quotation yet</span>
        </div>

        <div class="flex flex-col items-start justify-between gap-3 rounded-lg border border-warning-100 bg-warning-50 px-3 py-2.5 tablet:flex-row tablet:items-center">
          <div class="flex items-center gap-2 text-sm text-warning-700">
            <AlertTriangle class="h-4 w-4 shrink-0" />
            <span>Civil ID verification is a must</span>
            <StatusBadge
              v-if="civilIdDocument"
              :label="civilIdDocument.verificationStatus"
              :variant="getClientVerificationVariant(civilIdDocument.verificationStatus)"
            />
            <span v-else class="text-warning-700">-- not uploaded yet</span>
          </div>
          <BaseButton v-if="civilIdDocument" variant="ghost" size="sm" class="no-print" @click="viewCivilIdDocument">
            View Civil ID Attachment
          </BaseButton>
        </div>

        <div class="flex justify-end no-print">
          <BaseButton variant="secondary" size="sm" @click="emit('navigate-tab', 'quotation')">Go to Quotation</BaseButton>
        </div>
      </div>
    </Card>

    <Card v-if="stageContext === 'Contract'">
      <template #header>
        <h3 class="text-sm font-semibold text-text-primary">Contract</h3>
      </template>
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
          <div>
            <p class="text-xs text-text-muted">Quotation Number</p>
            <p class="text-sm font-medium text-text-primary">{{ contractQuotation?.quotationNo ?? '—' }}</p>
          </div>
          <div>
            <p class="text-xs text-text-muted">Quotation Date</p>
            <p class="text-sm font-medium text-text-primary">{{ contractQuotation ? formatDate(contractQuotation.issueDate) : '—' }}</p>
          </div>
          <div>
            <p class="text-xs text-text-muted">Quotation Amount</p>
            <p class="text-sm font-medium text-text-primary">{{ contractQuotation ? formatCurrency(contractQuotation.amount) : '—' }}</p>
          </div>
        </div>

        <div class="flex flex-col items-start justify-between gap-3 rounded-lg border border-warning-100 bg-warning-50 px-3 py-2.5 tablet:flex-row tablet:items-center">
          <div class="flex items-center gap-2 text-sm text-warning-700">
            <AlertTriangle class="h-4 w-4 shrink-0" />
            <span>Quotation approval is a must</span>
            <StatusBadge
              v-if="contractQuotation"
              :label="contractQuotation.status"
              :variant="contractQuotation.status === 'Approved' ? 'success' : contractQuotation.status === 'Rejected' ? 'danger' : 'neutral'"
            />
            <span v-else class="text-warning-700">-- no quotation linked</span>
          </div>
          <BaseButton v-if="contractQuotation" variant="ghost" size="sm" class="no-print" @click="emit('navigate-tab', 'quotation')">
            View Approved Quotation
          </BaseButton>
        </div>
      </div>
    </Card>

    <Card v-if="stageContext === 'Design'">
      <template #header>
        <h3 class="text-sm font-semibold text-text-primary">Design</h3>
      </template>
      <div class="flex flex-col gap-4">
        <div v-if="designDocuments.length > 0" class="flex flex-col gap-2">
          <div
            v-for="document in designDocuments"
            :key="document.id"
            class="flex items-center justify-between gap-3 rounded-lg border border-border-light p-3"
          >
            <span class="truncate text-sm text-text-secondary">{{ document.title }}</span>
            <StatusBadge :label="document.status" :variant="getDocumentStatusVariant(document.status)" />
          </div>
        </div>
        <p v-else class="text-sm text-text-muted">No design documents delivered yet.</p>

        <div class="flex justify-end no-print">
          <BaseButton variant="secondary" size="sm" @click="emit('navigate-tab', 'design')">Go to Documents</BaseButton>
        </div>
      </div>
    </Card>

    <Card v-if="stageContext === 'Government Submission'">
      <template #header>
        <h3 class="text-sm font-semibold text-text-primary">Required Documents</h3>
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
                View
              </BaseButton>
            </template>
            <BaseButton v-else variant="secondary" size="sm" class="no-print shrink-0" @click="openFillDialog(form)">
              Fill Form
            </BaseButton>
          </div>
        </div>
        <p v-else class="text-sm text-text-muted">
          No fillable forms are mapped to this project's service yet -- see Administration &gt; Service Document Map.
        </p>
      </div>
    </Card>

    <Card v-if="stageContext === 'Government Submission'">
      <template #header>
        <h3 class="text-sm font-semibold text-text-primary">Approvals &amp; Permits</h3>
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
                &middot; Last worked on {{ lastWorkedOnDate(submission) ? formatDate(lastWorkedOnDate(submission)!) : '—' }}
              </span>
            </div>
            <StatusBadge :label="submission.status" :variant="getSubmissionStatusVariant(submission.status)" />
          </div>
        </div>
        <p v-else class="text-sm text-text-muted">No approvals or permits filed yet.</p>

        <div class="flex justify-end no-print">
          <BaseButton variant="secondary" size="sm" @click="emit('navigate-tab', 'government')">Go to Documents</BaseButton>
        </div>
      </div>
    </Card>

    <div v-if="showScopeAndDetails" class="grid grid-cols-1 gap-6 laptop:grid-cols-2">
      <DetailPanel title="Project Details" :items="projectDetailItems" />
      <div class="flex flex-col gap-3">
        <DetailPanel title="Client Details" :items="clientDetailItems" />
        <div class="flex gap-2 no-print">
          <BaseButton
            v-if="client"
            variant="secondary"
            size="sm"
            :icon="MessageSquare"
            @click="router.push({ name: ROUTE_NAMES.MESSAGE_CENTRE, query: { clientId: client.id } })"
          >
            Message Client
          </BaseButton>
          <BaseButton
            v-if="client"
            variant="ghost"
            size="sm"
            @click="router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId: client.id } })"
          >
            View Full Profile
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
