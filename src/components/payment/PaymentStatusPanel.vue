<script setup lang="ts">
import { Banknote, RefreshCcw, Wallet } from '@lucide/vue'
import { ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import FinancialActionDialog from '@/components/payment/FinancialActionDialog.vue'
import ObligationActionDialog from '@/components/payment/ObligationActionDialog.vue'
import PaymentRecordsList from '@/components/payment/PaymentRecordsList.vue'
import PaymentSummaryCards from '@/components/payment/PaymentSummaryCards.vue'
import PaymentTimeline from '@/components/payment/PaymentTimeline.vue'
import RecordPaymentDialog from '@/components/payment/RecordPaymentDialog.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { usePaymentAgreements } from '@/composables/usePaymentAgreements'
import { usePaymentStore } from '@/stores/paymentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import { getAgreementStreamLabel } from '@/utils/paymentHelpers'
import type { AdjustmentType, FinancialAgreement, Payment, PaymentObligation, RecordPaymentInput } from '@/types/Payment'
import type { Project, ProjectWorkspaceTabKey } from '@/types/Project'

interface Props {
  projectId: string
  project: Project
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'navigate-tab': [tab: ProjectWorkspaceTabKey]
  'add-service': []
}>()

const { visibleStreams, agreementForStream, obligationsForStream, summaryForStream, outstandingObligationsForStream } = usePaymentAgreements(
  () => props.projectId,
  () => props.project,
)

const store = usePaymentStore()
const projectStore = useProjectStore()
// Matches every other create/edit/delete-style action in the app
// (Clients, Projects, Quotations, Contracts, Government Submissions) --
// an explicit acknowledgment dialog for actions that change money on
// record, not a toast that could be missed.
const resultDialogStore = useResultDialogStore()

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

const streamsWithAgreement = () => visibleStreams.value.filter((stream) => agreementForStream(stream))
const streamsMissingAgreement = () => visibleStreams.value.filter((stream) => !agreementForStream(stream))

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

async function handleRecordPayment(input: RecordPaymentInput, proofFile: File | undefined): Promise<void> {
  try {
    const payment = await store.recordPayment(input, 'Rajan Kumar')
    if (proofFile) {
      await store.attachPaymentProof(payment.id, proofFile, input.agreementId)
    }
    // Keeps the shared project store's cached data (e.g. amounts shown
    // elsewhere in the workspace) in sync with what was just recorded.
    await projectStore.refreshProject(props.projectId)
    resultDialogStore.showSuccess('Payment recorded', 'The payment schedule has been updated.')
    isRecordPaymentOpen.value = false
  } catch (error) {
    resultDialogStore.showError('Could not record payment', error instanceof Error ? error.message : 'Please try again.')
  }
}

async function handleDownloadProof(payment: Payment): Promise<void> {
  if (!payment.proofFileName) return
  try {
    await store.downloadPaymentProof(payment.id, payment.proofFileName)
  } catch (error) {
    resultDialogStore.showError('Could not download proof', error instanceof Error ? error.message : 'Please try again.')
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
      description="This project has no Design or Supervision work selected, so there's no payment status to track yet."
      action-label="Add Service"
      @action="emit('add-service')"
    />

    <EmptyState
      v-else-if="streamsWithAgreement().length === 0"
      :icon="Wallet"
      title="No payment plan defined yet"
      description="Define this project's payment plan before payments can be tracked here."
      action-label="Go to Payment Plan"
      @action="emit('navigate-tab', 'payment-plan')"
    />

    <template v-else>
      <p v-if="streamsMissingAgreement().length > 0" class="text-sm text-text-muted">
        Still missing a payment plan for {{ streamsMissingAgreement().map((s) => getAgreementStreamLabel(s)).join(' and ') }} --
        <button type="button" class="text-accent-600 underline" @click="emit('navigate-tab', 'payment-plan')">go to Payment Plan</button>.
      </p>

      <div v-for="stream in streamsWithAgreement()" :key="stream" class="flex flex-col gap-4">
        <div v-if="streamsWithAgreement().length > 1" class="flex items-center gap-2">
          <h3 class="text-sm font-semibold uppercase tracking-wide text-text-muted">{{ getAgreementStreamLabel(stream) }}</h3>
          <StatusBadge
            :label="agreementForStream(stream)!.status"
            :variant="agreementForStream(stream)!.status === 'Approved' ? 'success' : 'warning'"
          />
        </div>

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

        <PaymentRecordsList
          :payments="store.paymentsByAgreement[agreementForStream(stream)!.id] ?? []"
          :currency="agreementForStream(stream)!.currency"
          @download="handleDownloadProof"
        />
      </div>
    </template>

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
  </div>
</template>
