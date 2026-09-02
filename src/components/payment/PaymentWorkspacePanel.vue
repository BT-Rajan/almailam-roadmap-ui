<script setup lang="ts">
import { ArrowRight, Banknote, CheckCircle2, RefreshCcw, Wallet } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'

import AgreementFormDialog from '@/components/payment/AgreementFormDialog.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import FinancialActionDialog from '@/components/payment/FinancialActionDialog.vue'
import ObligationActionDialog from '@/components/payment/ObligationActionDialog.vue'
import PaymentHistoryPanel from '@/components/payment/PaymentHistoryPanel.vue'
import PaymentSummaryCards from '@/components/payment/PaymentSummaryCards.vue'
import PaymentTimeline from '@/components/payment/PaymentTimeline.vue'
import RecordPaymentDialog from '@/components/payment/RecordPaymentDialog.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { usePaymentStore } from '@/stores/paymentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import { computeObligationStatus, getAgreementStreamLabel } from '@/utils/paymentHelpers'
import type { AdjustmentType, AgreementStream, FinancialAgreement, PaymentObligation, RecordPaymentInput } from '@/types/Payment'
import type { Project, ProjectWorkspaceTabKey } from '@/types/Project'

interface Props {
  projectId: string
  project: Project
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
}>()

const store = usePaymentStore()
const projectStore = useProjectStore()
const quotationStore = useQuotationStore()
// Matches every other create/edit/delete-style action in the app
// (Clients, Projects, Quotations, Contracts, Government Submissions) --
// an explicit acknowledgment dialog for actions that change money on
// record, not a toast that could be missed.
const resultDialogStore = useResultDialogStore()

const isAgreementFormOpen = ref(false)
const agreementFormStream = ref<AgreementStream>('Design')
const isRecordPaymentOpen = ref(false)
const preselectedObligationId = ref<string | undefined>(undefined)
const financialActionMode = ref<'refund' | 'adjustment'>('refund')
const isFinancialActionOpen = ref(false)
const obligationActionMode = ref<'cancel' | 'waive'>('cancel')
const isObligationActionOpen = ref(false)
const targetObligation = ref<PaymentObligation | undefined>(undefined)
// Which agreement the currently-open Record Payment / Refund / Adjustment
// / Cancel / Waive dialog is acting on -- a project can have both a
// Design and a Supervision agreement at once (migration 0059), so unlike
// before there's no single implicit "the" agreement any of these can
// default to.
const activeAgreement = ref<FinancialAgreement | undefined>(undefined)

// A section is shown per billing stream this project actually includes
// (see project.includesDesign/includesSupervision) -- plus any stream
// that already has an agreement, in case that flag and the agreement's
// existence ever momentarily disagree.
const visibleStreams = computed<AgreementStream[]>(() => {
  const streams = new Set<AgreementStream>()
  if (props.project.includesDesign) streams.add('Design')
  if (props.project.includesSupervision) streams.add('Supervision')
  for (const agreement of store.agreements) {
    if (agreement.projectId === props.projectId) streams.add(agreement.stream)
  }
  return [...streams]
})

function agreementForStream(stream: AgreementStream): FinancialAgreement | undefined {
  return store.getAgreementByProject(props.projectId, stream)
}

function obligationsForStream(stream: AgreementStream): PaymentObligation[] {
  const agreement = agreementForStream(stream)
  return agreement ? store.obligationsForAgreement(agreement.id) : []
}

function summaryForStream(stream: AgreementStream) {
  const agreement = agreementForStream(stream)
  return agreement ? store.summaryForAgreement(agreement.id) : undefined
}

function outstandingObligationsForStream(stream: AgreementStream): PaymentObligation[] {
  return obligationsForStream(stream).filter((obligation) => {
    const status = computeObligationStatus(obligation)
    return status !== 'Paid' && status !== 'Cancelled' && status !== 'Waived'
  })
}

const agreementIds = computed(() =>
  visibleStreams.value.map((stream) => agreementForStream(stream)?.id).filter((id): id is string => Boolean(id)),
)

async function loadDetailIfNeeded(): Promise<void> {
  await Promise.all(agreementIds.value.map((id) => store.loadAgreementDetail(id)))
}

onMounted(loadDetailIfNeeded)
watch(agreementIds, loadDetailIfNeeded)

// The project's Approved quotation, if any -- used to pre-fill Total
// Contract Amount and Currency on the "Create Financial Agreement" form
// instead of leaving them blank for staff to re-type from the
// quotation that was just approved. Sourced from the quotation, not a
// signed contract: the Payment Plan stage (where an agreement actually
// gets created) comes *before* Contract now, so no contract exists yet
// to prefill from -- see project_service._assert_stage_exit_criteria's
// Payment Plan entry criterion, which requires exactly this same fact.
//
// Reads straight from quotationStore.quotations without loading it
// here -- ProjectWorkspacePage.vue's own loadData() already fetches
// this project's quotations before any tab (this one included) ever
// mounts. Re-fetching redundantly in an onMounted() here caused a real
// infinite mount/fetch loop with contractStore before this same fix was
// applied to it -- see git history -- so this deliberately doesn't
// repeat that mistake with quotationStore.
const approvedQuotation = computed(() => quotationStore.quotations.find((quotation) => quotation.status === 'Approved'))

// Every included stream's agreement has to exist and be Approved before
// "Advance to Contract" makes sense -- mirrors project_service._assert_
// stage_exit_criteria's own Payment Plan -> Contract check exactly, so
// this button only ever appears when that check would actually pass.
const allRequiredAgreementsApproved = computed(
  () => visibleStreams.value.length > 0 && visibleStreams.value.every((stream) => agreementForStream(stream)?.status === 'Approved'),
)

// Gates the explainer banner below -- once every included stream's
// agreement exists, the two-part structure it explains is no longer
// news to anyone looking at this tab, so it stops showing.
const anyAgreementMissing = computed(() => visibleStreams.value.some((stream) => !agreementForStream(stream)))

// Explains the project's payment plan up front, in plain terms, before
// staff start creating agreements -- only mentions whichever stream(s)
// this project actually includes (see visibleStreams).
const planExplainer = computed(() => {
  const parts: string[] = []
  if (visibleStreams.value.includes('Design')) {
    parts.push('a one-time Design & Permit fee, paid in full or split into up to 5 installments you control')
  }
  if (visibleStreams.value.includes('Supervision')) {
    parts.push('a monthly Supervision fee, billed pro-rata for partial months')
  }
  if (parts.length === 2) return `This project's payment plan has two parts: ${parts[0]}, and ${parts[1]}.`
  if (parts.length === 1) return `This project's payment plan is ${parts[0]}.`
  return ''
})

const isApprovingStream = ref<AgreementStream | undefined>(undefined)

function openCreateAgreement(stream: AgreementStream): void {
  agreementFormStream.value = stream
  isAgreementFormOpen.value = true
}

async function handleApproveAgreement(agreement: FinancialAgreement): Promise<void> {
  isApprovingStream.value = agreement.stream
  try {
    await store.approveAgreement(agreement.id)
    await projectStore.refreshProject(props.projectId)
    resultDialogStore.showSuccess(`${agreement.stream} agreement approved`, 'The payment plan is now approved.')
  } catch (error) {
    resultDialogStore.showError('Could not approve agreement', error instanceof Error ? error.message : 'Please try again.')
  } finally {
    isApprovingStream.value = undefined
  }
}

// Hands the already-approved quotation off via the store and switches
// to the Contract tab, which picks up the pending request and opens its
// New Contract dialog prefilled from it -- same mechanism
// ProjectQuotationTab.vue used to trigger itself before this hop moved
// here (see quotationStore.requestAdvanceToContract).
function handleAdvanceToContract(): void {
  if (!approvedQuotation.value) return
  quotationStore.requestAdvanceToContract(approvedQuotation.value.id)
  emit('navigate-tab', 'contract')
}

function openRecordPayment(agreement: FinancialAgreement, obligation?: PaymentObligation): void {
  activeAgreement.value = agreement
  preselectedObligationId.value = obligation?.id
  isRecordPaymentOpen.value = true
}

function openFinancialAction(agreement: FinancialAgreement, mode: 'refund' | 'adjustment'): void {
  activeAgreement.value = agreement
  financialActionMode.value = mode
  isFinancialActionOpen.value = true
}

function openObligationAction(agreement: FinancialAgreement, mode: 'cancel' | 'waive', obligation: PaymentObligation): void {
  activeAgreement.value = agreement
  obligationActionMode.value = mode
  targetObligation.value = obligation
  isObligationActionOpen.value = true
}

// Creating an agreement no longer advances the project by itself -- it
// starts as 'Draft' and still needs an explicit Approve (see
// handleApproveAgreement above and project_service._assert_stage_exit_
// criteria's Payment Plan -> Contract check) -- so this just closes the
// dialog and stays put rather than navigating anywhere.
async function handleCreateAgreement(input: Parameters<typeof store.createAgreement>[0]): Promise<void> {
  try {
    await store.createAgreement(input, 'Rajan Kumar')
    resultDialogStore.showSuccess('Financial agreement created', 'Review the payment schedule, then approve it to continue.')
    isAgreementFormOpen.value = false
  } catch {
    resultDialogStore.showError('Could not create agreement', 'Please try again.')
  }
}

async function handleRecordPayment(input: RecordPaymentInput): Promise<void> {
  try {
    await store.recordPayment(input, 'Rajan Kumar')
    // Keeps the shared project store's cached data (e.g. amounts shown
    // elsewhere in the workspace) in sync with what was just recorded.
    await projectStore.refreshProject(props.projectId)
    resultDialogStore.showSuccess('Payment recorded', 'The payment schedule has been updated.')
    isRecordPaymentOpen.value = false
  } catch {
    resultDialogStore.showError('Could not record payment', 'Please try again.')
  }
}

async function handleRefund(input: { obligationId: string; refundAmount: number; refundDate: string; reason: string; authorisingUser: string; reference?: string }): Promise<void> {
  if (!activeAgreement.value) return
  try {
    await store.recordRefund({ ...input, agreementId: activeAgreement.value.id })
    resultDialogStore.showSuccess('Refund recorded', 'The obligation balance has been updated.')
    isFinancialActionOpen.value = false
  } catch {
    resultDialogStore.showError('Could not record refund', 'Please try again.')
  }
}

async function handleAdjustment(input: { obligationId: string; type: AdjustmentType; amount: number; reason: string; authorisingUser: string }): Promise<void> {
  if (!activeAgreement.value) return
  try {
    await store.recordAdjustment({ ...input, agreementId: activeAgreement.value.id })
    resultDialogStore.showSuccess('Adjustment applied', 'The obligation amount has been updated.')
    isFinancialActionOpen.value = false
  } catch {
    resultDialogStore.showError('Could not apply adjustment', 'Please try again.')
  }
}

async function handleObligationActionConfirm(reason: string): Promise<void> {
  if (!activeAgreement.value || !targetObligation.value) return
  try {
    if (obligationActionMode.value === 'cancel') {
      await store.cancelObligation(targetObligation.value.id, activeAgreement.value.id, reason, 'Rajan Kumar')
      resultDialogStore.showSuccess('Obligation cancelled')
    } else {
      await store.waiveObligation(targetObligation.value.id, activeAgreement.value.id, reason, 'Rajan Kumar')
      resultDialogStore.showSuccess('Obligation waived')
    }
    isObligationActionOpen.value = false
  } catch {
    resultDialogStore.showError('Could not complete this action', 'Please try again.')
  }
}
</script>

<template>
  <div class="flex flex-col gap-8">
    <EmptyState
      v-if="visibleStreams.length === 0"
      :icon="Wallet"
      title="No billable services selected"
      description="This project has no Design or Supervision work selected, so there's no financial agreement to create yet."
    />

    <div class="flex flex-col gap-1">
      <h2 class="text-base font-semibold text-text-primary">Project Payment Plan</h2>
      <p v-if="anyAgreementMissing" class="text-sm text-text-muted">{{ planExplainer }} Every part has to be approved here before this project can move to Contract.</p>
    </div>

    <div
      v-if="allRequiredAgreementsApproved"
      class="flex flex-col items-start justify-between gap-3 rounded-lg border border-success-100 bg-success-50 px-4 py-3 tablet:flex-row tablet:items-center no-print"
    >
      <p class="text-sm text-success-700">Every required financial agreement is approved -- this project is ready for Contract.</p>
      <BaseButton size="sm" :icon="ArrowRight" @click="handleAdvanceToContract">Advance to Contract</BaseButton>
    </div>

    <div v-for="stream in visibleStreams" :key="stream" class="flex flex-col gap-4">
      <div v-if="visibleStreams.length > 1" class="flex items-center gap-2">
        <h3 class="text-sm font-semibold uppercase tracking-wide text-text-muted">{{ getAgreementStreamLabel(stream) }}</h3>
        <StatusBadge
          v-if="agreementForStream(stream)"
          :label="agreementForStream(stream)!.status"
          :variant="agreementForStream(stream)!.status === 'Approved' ? 'success' : 'warning'"
        />
      </div>

      <EmptyState
        v-if="!agreementForStream(stream)"
        :icon="Wallet"
        :title="`No ${getAgreementStreamLabel(stream)} payment plan yet`"
        :description="
          stream === 'Supervision'
            ? 'Create a Supervision agreement to generate its day-prorated monthly payment schedule for this project.'
            : 'Create a one-time payment plan for this project -- paid in full, or split into up to 5 installments you control.'
        "
        :action-label="`Create ${getAgreementStreamLabel(stream)} Payment Plan`"
        @action="openCreateAgreement(stream)"
      />

      <template v-else-if="summaryForStream(stream)">
        <div v-if="visibleStreams.length === 1" class="flex items-center justify-end no-print">
          <StatusBadge
            :label="agreementForStream(stream)!.status"
            :variant="agreementForStream(stream)!.status === 'Approved' ? 'success' : 'warning'"
          />
        </div>

        <PaymentSummaryCards :summary="summaryForStream(stream)!" :currency="agreementForStream(stream)!.currency" />

        <div class="flex flex-wrap items-center justify-end gap-2 no-print">
          <BaseButton
            v-if="agreementForStream(stream)!.status === 'Draft'"
            size="sm"
            :icon="CheckCircle2"
            :loading="isApprovingStream === stream"
            @click="handleApproveAgreement(agreementForStream(stream)!)"
          >
            Approve Payment Plan
          </BaseButton>
          <BaseButton variant="secondary" size="sm" :icon="Banknote" @click="openRecordPayment(agreementForStream(stream)!)">Record Payment</BaseButton>
          <BaseButton variant="ghost" size="sm" @click="openFinancialAction(agreementForStream(stream)!, 'refund')">Issue Refund</BaseButton>
          <BaseButton variant="ghost" size="sm" :icon="RefreshCcw" @click="openFinancialAction(agreementForStream(stream)!, 'adjustment')">Apply Adjustment</BaseButton>
        </div>

        <PaymentTimeline
          :obligations="obligationsForStream(stream)"
          :currency="agreementForStream(stream)!.currency"
          @record-payment="(obligation) => openRecordPayment(agreementForStream(stream)!, obligation)"
          @cancel="(obligation) => openObligationAction(agreementForStream(stream)!, 'cancel', obligation)"
          @waive="(obligation) => openObligationAction(agreementForStream(stream)!, 'waive', obligation)"
        />

        <PaymentHistoryPanel :events="store.auditEventsByAgreement[agreementForStream(stream)!.id] ?? []" />
      </template>
    </div>

    <RecordPaymentDialog
      v-if="activeAgreement"
      v-model="isRecordPaymentOpen"
      :agreement-id="activeAgreement.id"
      :project-id="projectId"
      :currency="activeAgreement.currency"
      :outstanding-obligations="outstandingObligationsForStream(activeAgreement.stream)"
      :preselected-obligation-id="preselectedObligationId"
      :is-submitting="store.isSubmitting"
      @submit="handleRecordPayment"
    />

    <FinancialActionDialog
      v-if="activeAgreement"
      v-model="isFinancialActionOpen"
      :mode="financialActionMode"
      :obligations="obligationsForStream(activeAgreement.stream)"
      :currency="activeAgreement.currency"
      :is-submitting="store.isSubmitting"
      @submit-refund="handleRefund"
      @submit-adjustment="handleAdjustment"
    />

    <ObligationActionDialog
      v-model="isObligationActionOpen"
      :mode="obligationActionMode"
      :obligation="targetObligation"
      :is-submitting="store.isSubmitting"
      @confirm="handleObligationActionConfirm"
    />

    <AgreementFormDialog
      v-model="isAgreementFormOpen"
      :project-id="projectId"
      :stream="agreementFormStream"
      :approved-contract="
        approvedQuotation
          ? { quotationNo: approvedQuotation.quotationNo, contractValue: approvedQuotation.amount, currency: approvedQuotation.currency }
          : undefined
      "
      :is-submitting="store.isSubmitting"
      @submit="handleCreateAgreement"
    />
  </div>
</template>
