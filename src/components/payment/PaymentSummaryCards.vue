<script setup lang="ts">
import { AlertTriangle, Banknote, CalendarClock, CheckCircle2, FileSpreadsheet, Wallet } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import InfoPanel from '@/components/common/InfoPanel.vue'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import type { FinancialSummary } from '@/types/Payment'

interface Props {
  summary: FinancialSummary
  currency: string
}

const props = defineProps<Props>()

const { t } = useI18n()

const nextPaymentValue = computed(() => {
  if (!props.summary.nextPaymentObligation) return t('payment.summaryCards.fullySettled')
  return formatCurrency(props.summary.nextPaymentObligation.amountDue - props.summary.nextPaymentObligation.amountReceived, props.currency)
})

const nextPaymentDateLabel = computed(() => {
  if (!props.summary.nextPaymentObligation) return t('payment.summaryCards.noOutstandingObligations')
  const dueLabel = formatDate(props.summary.nextPaymentObligation.dueDate)
  if (props.summary.nextPaymentIsOverdue) {
    const daysOverdue = Math.abs(props.summary.nextPaymentDaysUntilDue ?? 0)
    return t('payment.summaryCards.overdueBy', { date: dueLabel, days: daysOverdue }, daysOverdue)
  }
  return t('payment.summaryCards.due', { date: dueLabel })
})

// Waived/cancelled obligations and adjustment drift are excluded from
// the 5 cards above by design (they're not still payable, or they're an
// accounting variance rather than a balance) -- surfaced here instead of
// silently vanishing from the total, and only shown when non-zero so the
// common case (no waivers, no drift) stays a clean 5-card row.
const totalForgiven = computed(() => props.summary.totalWaived + props.summary.totalCancelled)
const hasScheduleVariance = computed(() => Math.abs(props.summary.scheduleVariance) > 0.01)
</script>

<template>
  <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-3 desktop:grid-cols-6">
    <InfoPanel
      v-if="summary.estimateAmount !== null"
      :label="t('payment.summaryCards.estimateAmount')"
      :value="formatCurrency(summary.estimateAmount, currency)"
      :icon="FileSpreadsheet"
      color="neutral"
    />
    <InfoPanel :label="t('payment.summaryCards.contractValue')" :value="formatCurrency(summary.contractAmount, currency)" :icon="Wallet" color="primary" />
    <InfoPanel :label="t('payment.summaryCards.totalReceived')" :value="formatCurrency(summary.totalReceived, currency)" :icon="CheckCircle2" color="success" />
    <InfoPanel :label="t('payment.summaryCards.totalPending')" :value="formatCurrency(summary.totalPending, currency)" :icon="Banknote" color="warning" />
    <InfoPanel :label="t('payment.summaryCards.totalOverdue')" :value="formatCurrency(summary.totalOverdue, currency)" :icon="AlertTriangle" :color="summary.totalOverdue > 0 ? 'danger' : 'neutral'" />
    <InfoPanel :label="t('payment.summaryCards.nextPayment')" :value="nextPaymentValue" :icon="CalendarClock" :color="summary.nextPaymentIsOverdue ? 'danger' : 'info'" />
  </div>
  <p v-if="summary.nextPaymentObligation" class="mt-2 text-xs" :class="summary.nextPaymentIsOverdue ? 'font-medium text-danger-600' : 'text-text-muted'">
    {{ nextPaymentDateLabel }}
  </p>
  <p v-if="totalForgiven > 0" class="mt-1 text-xs text-text-muted">{{ t('payment.summaryCards.waivedCancelledExcluded', { amount: formatCurrency(totalForgiven, currency) }) }}</p>
  <p v-if="hasScheduleVariance" class="mt-1 text-xs text-text-muted">{{ t('payment.summaryCards.scheduleVarianceNote', { amount: formatCurrency(Math.abs(summary.scheduleVariance), currency) }) }}</p>
</template>
