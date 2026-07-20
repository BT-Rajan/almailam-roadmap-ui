<script setup lang="ts">
import { AlertTriangle, Banknote, CalendarClock, CheckCircle2, Wallet } from '@lucide/vue'
import { computed } from 'vue'

import InfoPanel from '@/components/common/InfoPanel.vue'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import type { FinancialSummary } from '@/types/Payment'

interface Props {
  summary: FinancialSummary
  currency: string
}

const props = defineProps<Props>()

const nextPaymentValue = computed(() => {
  if (!props.summary.nextPaymentObligation) return 'Fully settled'
  return formatCurrency(props.summary.nextPaymentObligation.amountDue - props.summary.nextPaymentObligation.amountReceived, props.currency)
})

const nextPaymentDateLabel = computed(() => {
  if (!props.summary.nextPaymentObligation) return 'No outstanding obligations'
  const dueLabel = formatDate(props.summary.nextPaymentObligation.dueDate)
  if (props.summary.nextPaymentIsOverdue) {
    const daysOverdue = Math.abs(props.summary.nextPaymentDaysUntilDue ?? 0)
    return `OVERDUE — ${dueLabel} (${daysOverdue} day${daysOverdue === 1 ? '' : 's'} overdue)`
  }
  return `Due ${dueLabel}`
})
</script>

<template>
  <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2 laptop:grid-cols-5">
    <InfoPanel label="Contract Value" :value="formatCurrency(summary.contractAmount, currency)" :icon="Wallet" color="primary" />
    <InfoPanel label="Total Received" :value="formatCurrency(summary.totalReceived, currency)" :icon="CheckCircle2" color="success" />
    <InfoPanel label="Total Pending" :value="formatCurrency(summary.totalPending, currency)" :icon="Banknote" color="warning" />
    <InfoPanel label="Total Overdue" :value="formatCurrency(summary.totalOverdue, currency)" :icon="AlertTriangle" :color="summary.totalOverdue > 0 ? 'danger' : 'neutral'" />
    <InfoPanel label="Next Payment" :value="nextPaymentValue" :icon="CalendarClock" :color="summary.nextPaymentIsOverdue ? 'danger' : 'info'" />
  </div>
  <p v-if="summary.nextPaymentObligation" class="mt-2 text-xs" :class="summary.nextPaymentIsOverdue ? 'font-medium text-danger-600' : 'text-neutral-500'">
    {{ nextPaymentDateLabel }}
  </p>
</template>
