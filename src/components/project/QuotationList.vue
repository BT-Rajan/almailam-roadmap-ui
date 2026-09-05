<script setup lang="ts">
import { FileText } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { getQuotationStatusVariant } from '@/utils/quotationHelpers'
import type { Quotation } from '@/types/Quotation'

interface Props {
  quotations: Quotation[]
  selectedQuotationId?: string
}

withDefaults(defineProps<Props>(), {
  selectedQuotationId: undefined,
})

const emit = defineEmits<{
  select: [quotationId: string]
}>()

const { t } = useI18n()

const QUOTATION_STATUS_KEYS: Record<Quotation['status'], string> = {
  Draft: 'project.quotationStatus.draft',
  Approved: 'project.quotationStatus.approved',
  Rejected: 'project.quotationStatus.rejected',
  Expired: 'project.quotationStatus.expired',
}
</script>

<template>
  <Card :padded="false">
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('project.quotationList.title') }}</h3>
    </template>

    <EmptyState
      v-if="quotations.length === 0"
      :icon="FileText"
      :title="t('project.quotationList.emptyTitle')"
      :description="t('project.quotationList.emptyDescription')"
    />

    <ul v-else class="divide-y divide-border-light">
      <li v-for="quotation in [...quotations].reverse()" :key="quotation.id">
        <button
          type="button"
          class="flex w-full flex-col gap-1.5 px-5 py-4 text-left transition-colors duration-fast"
          :class="quotation.id === selectedQuotationId ? 'bg-bg-selected' : 'hover:bg-bg-hover'"
          :aria-current="quotation.id === selectedQuotationId ? 'true' : undefined"
          @click="emit('select', quotation.id)"
        >
          <div class="flex items-center justify-between gap-3">
            <span class="text-sm font-semibold text-text-primary">{{ quotation.quotationNo }}</span>
            <StatusBadge :label="t(QUOTATION_STATUS_KEYS[quotation.status])" :variant="getQuotationStatusVariant(quotation.status)" size="sm" />
          </div>
          <p class="text-xs text-text-muted">{{ t('project.quotationList.revisionIssued', { revision: quotation.revision, date: formatDate(quotation.issueDate) }) }}</p>
          <p class="text-sm font-medium text-text-secondary">{{ formatCurrency(quotation.amount, quotation.currency) }}</p>
        </button>
      </li>
    </ul>
  </Card>
</template>
