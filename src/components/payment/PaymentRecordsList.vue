<script setup lang="ts">
import { Download } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

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

const { t } = useI18n()

const PAYMENT_MODE_LABEL_KEYS: Record<string, string> = {
  Cash: 'payment.paymentMode.cash',
  'Bank Transfer': 'payment.paymentMode.bankTransfer',
  'Credit Card': 'payment.paymentMode.creditCard',
  'Debit Card': 'payment.paymentMode.debitCard',
  'Online Payment': 'payment.paymentMode.onlinePayment',
  Cheque: 'payment.paymentMode.cheque',
  Other: 'payment.paymentMode.other',
}
function paymentModeLabel(mode: string): string {
  return t(PAYMENT_MODE_LABEL_KEYS[mode] ?? mode)
}
</script>

<template>
  <Card :padded="false">
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('payment.recordsList.title') }}</h3>
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
    <EmptyState v-if="payments.length === 0" :title="t('payment.recordsList.emptyTitle')" :description="t('payment.recordsList.emptyDescription')" />

    <ul v-else class="divide-y divide-border-light">
      <li v-for="payment in payments" :key="payment.id" class="flex flex-wrap items-center justify-between gap-3 px-4 py-3">
        <div class="flex flex-col gap-0.5">
          <p class="text-sm font-medium text-text-primary">{{ formatCurrency(payment.amountReceived, currency) }} &middot; {{ paymentModeLabel(payment.paymentMode) }}</p>
          <p class="text-xs text-text-muted">
            {{ formatDate(payment.paymentDate) }} &middot; {{ t('payment.recordsList.payer', { payer: payment.payer }) }}
            <span v-if="payment.referenceNumber"> &middot; {{ t('payment.recordsList.reference', { reference: payment.referenceNumber }) }}</span>
          </p>
        </div>

        <div class="flex items-center gap-2">
          <span v-if="payment.proofFileName" class="max-w-[12rem] truncate text-xs text-text-muted" :title="payment.proofFileName">
            {{ payment.proofFileName }}
          </span>
          <IconButton
            v-if="payment.proofFileName"
            :icon="Download"
            :label="t('payment.recordsList.downloadProof')"
            size="sm"
            @click="$emit('download', payment)"
          />
          <span v-else class="text-xs text-text-muted">{{ t('payment.recordsList.noProofAttached') }}</span>
        </div>
      </li>
    </ul>
  </Card>
</template>
