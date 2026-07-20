<script setup lang="ts">
import { computed } from 'vue'

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

const COLUMNS: SmartTableColumn<ObligationRow>[] = [
  { key: 'sequenceNumber', label: '#', width: '48px' },
  { key: 'description', label: 'Payment' },
  { key: 'dueDate', label: 'Due Date' },
  { key: 'amountDue', label: 'Amount', align: 'right' },
  { key: 'amountReceived', label: 'Received', align: 'right' },
  { key: 'amountPending', label: 'Pending', align: 'right' },
  { key: 'status', label: 'Status' },
]

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
</script>

<template>
  <Card :padded="false">
    <template #header>
      <h3 class="text-sm font-semibold text-neutral-800">Payment Timeline</h3>
    </template>

    <SmartTable :columns="COLUMNS" :rows="rows" row-key="id" :searchable="false">
      <template #cell-amountDue="{ value }">
        {{ formatCurrency(value as number, currency) }}
      </template>
      <template #cell-amountReceived="{ value }">
        {{ formatCurrency(value as number, currency) }}
      </template>
      <template #cell-amountPending="{ value }">
        {{ formatCurrency(value as number, currency) }}
      </template>
      <template #cell-status="{ value }">
        <StatusBadge :label="value as string" :variant="getObligationStatusVariant(value as ObligationStatus)" />
      </template>
      <template #row-actions="{ row }">
        <div v-if="!isSettled((row as ObligationRow).status)" class="flex justify-end gap-2">
          <BaseButton variant="ghost" size="sm" @click="emit('recordPayment', getObligation(row as ObligationRow)!)">Record Payment</BaseButton>
          <BaseButton variant="ghost" size="sm" @click="emit('waive', getObligation(row as ObligationRow)!)">Waive</BaseButton>
          <BaseButton variant="ghost" size="sm" @click="emit('cancel', getObligation(row as ObligationRow)!)">Cancel</BaseButton>
        </div>
      </template>
    </SmartTable>
  </Card>
</template>
