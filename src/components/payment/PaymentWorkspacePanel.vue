<script setup lang="ts">
import { Banknote, RefreshCcw, Wallet } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'

import AgreementFormDrawer from '@/components/payment/AgreementFormDrawer.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import FinancialActionDrawer from '@/components/payment/FinancialActionDrawer.vue'
import ObligationActionDialog from '@/components/payment/ObligationActionDialog.vue'
import PaymentHistoryPanel from '@/components/payment/PaymentHistoryPanel.vue'
import PaymentSummaryCards from '@/components/payment/PaymentSummaryCards.vue'
import PaymentTimeline from '@/components/payment/PaymentTimeline.vue'
import RecordPaymentDrawer from '@/components/payment/RecordPaymentDrawer.vue'
import { useToast } from '@/composables/useToast'
import { usePaymentStore } from '@/stores/paymentStore'
import { computeObligationStatus } from '@/utils/paymentHelpers'
import type { AdjustmentType, PaymentObligation, RecordPaymentInput } from '@/types/Payment'

interface Props {
  projectId: string
}

const props = defineProps<Props>()
const store = usePaymentStore()
const toast = useToast()

const isAgreementFormOpen = ref(false)
const isRecordPaymentOpen = ref(false)
const preselectedObligationId = ref<string | undefined>(undefined)
const financialActionMode = ref<'refund' | 'adjustment'>('refund')
const isFinancialActionOpen = ref(false)
const obligationActionMode = ref<'cancel' | 'waive'>('cancel')
const isObligationActionOpen = ref(false)
const targetObligation = ref<PaymentObligation | undefined>(undefined)

const agreement = computed(() => store.getAgreementByProject(props.projectId))
const obligations = computed(() => (agreement.value ? store.obligationsForAgreement(agreement.value.id) : []))
const summary = computed(() => (agreement.value ? store.summaryForAgreement(agreement.value.id) : undefined))
const auditEvents = computed(() => (agreement.value ? (store.auditEventsByAgreement[agreement.value.id] ?? []) : []))

const outstandingObligations = computed(() =>
  obligations.value.filter((obligation) => {
    const status = computeObligationStatus(obligation)
    return status !== 'Paid' && status !== 'Cancelled' && status !== 'Waived'
  }),
)

async function loadDetailIfNeeded(): Promise<void> {
  if (agreement.value) await store.loadAgreementDetail(agreement.value.id)
}

onMounted(loadDetailIfNeeded)
watch(agreement, loadDetailIfNeeded)

function openRecordPayment(obligation?: PaymentObligation): void {
  preselectedObligationId.value = obligation?.id
  isRecordPaymentOpen.value = true
}

function openFinancialAction(mode: 'refund' | 'adjustment'): void {
  financialActionMode.value = mode
  isFinancialActionOpen.value = true
}

function openObligationAction(mode: 'cancel' | 'waive', obligation: PaymentObligation): void {
  obligationActionMode.value = mode
  targetObligation.value = obligation
  isObligationActionOpen.value = true
}

async function handleCreateAgreement(input: Parameters<typeof store.createAgreement>[0]): Promise<void> {
  try {
    await store.createAgreement(input, 'Rajan Kumar')
    toast.success('Financial agreement created', 'The payment schedule has been generated.')
    isAgreementFormOpen.value = false
  } catch {
    toast.error('Could not create agreement', 'Please try again.')
  }
}

async function handleRecordPayment(input: RecordPaymentInput): Promise<void> {
  try {
    await store.recordPayment(input, 'Rajan Kumar')
    toast.success('Payment recorded', 'The payment schedule has been updated.')
    isRecordPaymentOpen.value = false
  } catch {
    toast.error('Could not record payment', 'Please try again.')
  }
}

async function handleRefund(input: { obligationId: string; refundAmount: number; refundDate: string; reason: string; authorisingUser: string; reference?: string }): Promise<void> {
  if (!agreement.value) return
  try {
    await store.recordRefund({ ...input, agreementId: agreement.value.id })
    toast.success('Refund recorded', 'The obligation balance has been updated.')
    isFinancialActionOpen.value = false
  } catch {
    toast.error('Could not record refund', 'Please try again.')
  }
}

async function handleAdjustment(input: { obligationId: string; type: AdjustmentType; amount: number; reason: string; authorisingUser: string }): Promise<void> {
  if (!agreement.value) return
  try {
    await store.recordAdjustment({ ...input, agreementId: agreement.value.id })
    toast.success('Adjustment applied', 'The obligation amount has been updated.')
    isFinancialActionOpen.value = false
  } catch {
    toast.error('Could not apply adjustment', 'Please try again.')
  }
}

async function handleObligationActionConfirm(reason: string): Promise<void> {
  if (!agreement.value || !targetObligation.value) return
  try {
    if (obligationActionMode.value === 'cancel') {
      await store.cancelObligation(targetObligation.value.id, agreement.value.id, reason, 'Rajan Kumar')
      toast.success('Obligation cancelled')
    } else {
      await store.waiveObligation(targetObligation.value.id, agreement.value.id, reason, 'Rajan Kumar')
      toast.success('Obligation waived')
    }
    isObligationActionOpen.value = false
  } catch {
    toast.error('Could not complete this action', 'Please try again.')
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <EmptyState
      v-if="!agreement"
      :icon="Wallet"
      title="No financial agreement yet"
      description="Create a financial agreement to start tracking the contract value, payment schedule, and collections for this project."
      action-label="Create Financial Agreement"
      @action="isAgreementFormOpen = true"
    />

    <template v-else-if="summary">
      <PaymentSummaryCards :summary="summary" :currency="agreement.currency" />

      <div class="flex flex-wrap items-center justify-end gap-2 no-print">
        <BaseButton variant="secondary" size="sm" :icon="Banknote" @click="openRecordPayment()">Record Payment</BaseButton>
        <BaseButton variant="ghost" size="sm" @click="openFinancialAction('refund')">Issue Refund</BaseButton>
        <BaseButton variant="ghost" size="sm" :icon="RefreshCcw" @click="openFinancialAction('adjustment')">Apply Adjustment</BaseButton>
      </div>

      <PaymentTimeline
        :obligations="obligations"
        :currency="agreement.currency"
        @record-payment="openRecordPayment"
        @cancel="(obligation) => openObligationAction('cancel', obligation)"
        @waive="(obligation) => openObligationAction('waive', obligation)"
      />

      <PaymentHistoryPanel :events="auditEvents" />

      <RecordPaymentDrawer
        v-model="isRecordPaymentOpen"
        :agreement-id="agreement.id"
        :project-id="projectId"
        :currency="agreement.currency"
        :outstanding-obligations="outstandingObligations"
        :preselected-obligation-id="preselectedObligationId"
        :is-submitting="store.isSubmitting"
        @submit="handleRecordPayment"
      />

      <FinancialActionDrawer
        v-model="isFinancialActionOpen"
        :mode="financialActionMode"
        :obligations="obligations"
        :currency="agreement.currency"
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
    </template>

    <AgreementFormDrawer v-model="isAgreementFormOpen" :project-id="projectId" :is-submitting="store.isSubmitting" @submit="handleCreateAgreement" />
  </div>
</template>
