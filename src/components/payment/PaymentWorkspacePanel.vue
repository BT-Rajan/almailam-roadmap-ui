<script setup lang="ts">
import { Banknote, RefreshCcw, Wallet } from '@lucide/vue'
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
import { usePaymentStore } from '@/stores/paymentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import { computeObligationStatus } from '@/utils/paymentHelpers'
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

function openCreateAgreement(stream: AgreementStream): void {
  agreementFormStream.value = stream
  isAgreementFormOpen.value = true
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

// Once the payment configuration (the financial agreement) is saved,
// the project is ready to move on to Design/Supervision (see
// project_service._assert_stage_exit_criteria's "Contract" -> [Design]/
// [Supervision] check) -- follow it there rather than leaving staff on
// the Payments tab.
async function handleCreateAgreement(input: Parameters<typeof store.createAgreement>[0]): Promise<void> {
  try {
    await store.createAgreement(input, 'Rajan Kumar')
    // The shared project store's cached stage is what the header badge
    // and Workflow Progress stepper read -- paymentStore's own auto-
    // advance on the backend doesn't update it on its own.
    await projectStore.refreshProject(props.projectId)
    resultDialogStore.showSuccess('Financial agreement created', 'The payment schedule has been generated.')
    isAgreementFormOpen.value = false
    emit('navigate-tab', agreementFormStream.value === 'Supervision' ? 'supervision' : 'design')
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

    <div v-for="stream in visibleStreams" :key="stream" class="flex flex-col gap-4">
      <h3 v-if="visibleStreams.length > 1" class="text-sm font-semibold uppercase tracking-wide text-text-muted">{{ stream }}</h3>

      <EmptyState
        v-if="!agreementForStream(stream)"
        :icon="Wallet"
        :title="`No ${stream} financial agreement yet`"
        :description="
          stream === 'Supervision'
            ? 'Create a Supervision agreement to generate its day-prorated monthly payment schedule for this project.'
            : 'Create a financial agreement to start tracking the contract value, payment schedule, and collections for this project.'
        "
        :action-label="`Create ${stream} Agreement`"
        @action="openCreateAgreement(stream)"
      />

      <template v-else-if="summaryForStream(stream)">
        <PaymentSummaryCards :summary="summaryForStream(stream)!" :currency="agreementForStream(stream)!.currency" />

        <div class="flex flex-wrap items-center justify-end gap-2 no-print">
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
      :is-submitting="store.isSubmitting"
      @submit="handleCreateAgreement"
    />
  </div>
</template>
