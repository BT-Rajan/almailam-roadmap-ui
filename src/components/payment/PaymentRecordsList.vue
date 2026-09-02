<script setup lang="ts">
import { Download } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import type { Payment } from '@/types/Payment'

interface Props {
  payments: Payment[]
  currency: string
}

defineProps<Props>()

defineEmits<{
  download: [payment: Payment]
}>()
</script>

<template>
  <Card :padded="false">
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">Recorded Payments</h3>
    </template>

    <!--
      Deliberately read-only -- no edit or delete action anywhere in this
      list. A recorded payment is immutable once submitted (the backend
      has no update/delete endpoint for it either); a correction goes
      through a separate Refund or Adjustment against the obligation
      instead, each its own audit-logged record. Attaching proof after
      the fact is the one addition still allowed, from the Record
      Payment dialog at the time it's created.
    -->
    <EmptyState v-if="payments.length === 0" title="No payments recorded yet" description="Payments recorded against this plan will appear here and can never be edited or removed." />

    <ul v-else class="divide-y divide-border-light">
      <li v-for="payment in payments" :key="payment.id" class="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div class="flex flex-col gap-0.5">
          <p class="text-sm font-medium text-text-primary">{{ formatCurrency(payment.amountReceived, currency) }} &middot; {{ payment.paymentMode }}</p>
          <p class="text-xs text-text-muted">
            {{ formatDate(payment.paymentDate) }} &middot; Payer: {{ payment.payer }}
            <span v-if="payment.referenceNumber"> &middot; Ref: {{ payment.referenceNumber }}</span>
          </p>
        </div>

        <div class="flex items-center gap-2">
          <span v-if="payment.proofFileName" class="max-w-[12rem] truncate text-xs text-text-muted" :title="payment.proofFileName">
            {{ payment.proofFileName }}
          </span>
          <IconButton
            v-if="payment.proofFileName"
            :icon="Download"
            label="Download payment proof"
            size="sm"
            @click="$emit('download', payment)"
          />
          <span v-else class="text-xs text-text-muted">No proof attached</span>
        </div>
      </li>
    </ul>
  </Card>
</template>
