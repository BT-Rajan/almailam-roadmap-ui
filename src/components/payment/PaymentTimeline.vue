<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { computeObligationStatus, getObligationStatusVariant } from '@/utils/paymentHelpers'
import type { ObligationStatus, PaymentObligation } from '@/types/Payment'
import type { SmartTableColumn } from '@/types/Table'

interface Props {
  obligations: PaymentObligation[]
  currency: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  recordPayment: [obligation: PaymentObligation]
  cancel: [obligation: PaymentObligation]
  waive: [obligation: PaymentObligation]
}>()

const { t } = useI18n()

interface ObligationRow {
  [key: string]: unknown
  id: string
  sequenceNumber: number
  description: string
  dueDate: string
  amountDue: number
  amountReceived: number
  amountPending: number
  status: string
}

const COLUMNS = computed<SmartTableColumn<ObligationRow>[]>(() => [
  { key: 'sequenceNumber', label: t('payment.timeline.columns.number'), width: '48px' },
  { key: 'description', label: t('payment.timeline.columns.payment') },
  { key: 'dueDate', label: t('payment.timeline.columns.dueDate') },
  { key: 'amountDue', label: t('payment.timeline.columns.amount'), align: 'right' },
  { key: 'amountReceived', label: t('payment.timeline.columns.received'), align: 'right' },
  { key: 'amountPending', label: t('payment.timeline.columns.pending'), align: 'right' },
  { key: 'status', label: t('payment.timeline.columns.status') },
])

const OBLIGATION_STATUS_LABEL_KEYS: Record<string, string> = {
  Scheduled: 'payment.obligationStatus.scheduled',
  Due: 'payment.obligationStatus.due',
  'Partially Paid': 'payment.obligationStatus.partiallyPaid',
  Paid: 'payment.obligationStatus.paid',
  Overdue: 'payment.obligationStatus.overdue',
  'Partially Overdue': 'payment.obligationStatus.partiallyOverdue',
  Cancelled: 'payment.obligationStatus.cancelled',
  Waived: 'payment.obligationStatus.waived',
}
function obligationStatusLabel(status: string): string {
  return t(OBLIGATION_STATUS_LABEL_KEYS[status] ?? status)
}

const rows = computed<ObligationRow[]>(() =>
  props.obligations.map((obligation) => ({
    id: obligation.id,
    sequenceNumber: obligation.sequenceNumber,
    description: obligation.description,
    dueDate: formatDate(obligation.dueDate),
    amountDue: obligation.amountDue,
    amountReceived: obligation.amountReceived,
    amountPending: Math.max(0, obligation.amountDue - obligation.amountReceived),
    status: computeObligationStatus(obligation),
  })),
)

function getObligation(row: ObligationRow): PaymentObligation | undefined {
  return props.obligations.find((obligation) => obligation.id === row.id)
}

function isSettled(status: string): boolean {
  return status === 'Paid' || status === 'Cancelled' || status === 'Waived'
}

function isOverdueRow(status: string): boolean {
  return status === 'Overdue' || status === 'Partially Overdue'
}
</script>

<template>
  <Card :padded="false">
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('payment.timeline.title') }}</h3>
    </template>

    <SmartTable :columns="COLUMNS" :rows="rows" row-key="id" :searchable="false">
      <template #cell-dueDate="{ row, value }">
        <span :class="isOverdueRow((row as ObligationRow).status) ? 'font-semibold text-danger-600' : ''">{{ value }}</span>
      </template>
      <template #cell-amountDue="{ value }">
        {{ formatCurrency(value as number, currency) }}
      </template>
      <template #cell-amountReceived="{ value }">
        {{ formatCurrency(value as number, currency) }}
      </template>
      <template #cell-amountPending="{ row, value }">
        <span :class="isOverdueRow((row as ObligationRow).status) ? 'font-semibold text-danger-600' : ''">
          {{ formatCurrency(value as number, currency) }}
        </span>
      </template>
      <template #cell-status="{ value }">
        <StatusBadge :label="obligationStatusLabel(value as string)" :variant="getObligationStatusVariant(value as ObligationStatus)" />
      </template>
      <template #row-actions="{ row }">
        <div v-if="!isSettled((row as ObligationRow).status)" class="flex justify-end gap-2">
          <BaseButton variant="ghost" size="sm" @click="emit('recordPayment', getObligation(row as ObligationRow)!)">{{ t('payment.timeline.recordPayment') }}</BaseButton>
          <BaseButton variant="ghost" size="sm" @click="emit('waive', getObligation(row as ObligationRow)!)">{{ t('payment.timeline.waive') }}</BaseButton>
          <BaseButton variant="ghost" size="sm" @click="emit('cancel', getObligation(row as ObligationRow)!)">{{ t('payment.timeline.cancel') }}</BaseButton>
        </div>
      </template>
    </SmartTable>
  </Card>
</template>
