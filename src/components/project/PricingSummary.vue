<script setup lang="ts">
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import Divider from '@/components/common/Divider.vue'
import { formatCurrency } from '@/utils/currencyFormatter'
import { calculateQuotationPricing } from '@/utils/quotationHelpers'
import type { Quotation } from '@/types/Quotation'

interface Props {
  quotation: Quotation
}

const props = defineProps<Props>()

const pricing = computed(() => calculateQuotationPricing(props.quotation))
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">Pricing Summary</h3>
    </template>

    <div class="flex flex-col gap-3 text-sm">
      <div class="flex items-center justify-between text-text-secondary">
        <span>Subtotal</span>
        <span class="font-medium text-text-primary">{{ formatCurrency(pricing.subtotal, quotation.currency) }}</span>
      </div>

      <div v-if="pricing.discount > 0" class="flex items-center justify-between text-text-secondary">
        <span>Discount</span>
        <span class="font-medium text-danger-700">-{{ formatCurrency(pricing.discount, quotation.currency) }}</span>
      </div>

      <div class="flex items-center justify-between text-text-secondary">
        <span>VAT ({{ pricing.taxRatePercent }}%)</span>
        <span class="font-medium text-text-primary">{{ formatCurrency(pricing.taxAmount, quotation.currency) }}</span>
      </div>

      <Divider />

      <div class="flex items-center justify-between">
        <span class="text-sm font-semibold text-text-primary">Total Amount</span>
        <span class="text-lg font-semibold text-primary-700">{{ formatCurrency(pricing.total, quotation.currency) }}</span>
      </div>
    </div>
  </Card>
</template>
