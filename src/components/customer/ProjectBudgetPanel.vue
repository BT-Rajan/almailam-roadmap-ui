<script setup lang="ts">
import { Wallet } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { ProjectBudget } from '@/types/CustomerPortal'
import { formatCurrency } from '@/utils/currencyFormatter'
import { isPastDate } from '@/utils/dateFormatter'

const props = defineProps<{
  budget: ProjectBudget | null
}>()

const { t } = useI18n()

const paidPercent = computed(() => {
  if (!props.budget || props.budget.contractAmount <= 0) return 0
  return Math.min(100, Math.round((props.budget.totalPaid / props.budget.contractAmount) * 100))
})
</script>

<template>
  <Card>
    <template #header>
      <h2 class="text-xl font-semibold text-text-primary">{{ t('customer.budgetPanel.title') }}</h2>
    </template>

    <EmptyState
      v-if="!budget"
      :icon="Wallet"
      :title="t('customer.budgetPanel.emptyTitle')"
      :description="t('customer.budgetPanel.emptyDescription')"
    />

    <div v-else class="flex flex-col gap-5">
      <div class="grid grid-cols-2 gap-4 tablet:grid-cols-3">
        <div>
          <p class="text-xs text-text-secondary">{{ t('customer.budgetPanel.contractAmount') }}</p>
          <p class="mt-0.5 text-lg font-semibold text-text-primary">{{ formatCurrency(budget.contractAmount, budget.currency) }}</p>
        </div>
        <div>
          <p class="text-xs text-text-secondary">{{ t('customer.budgetPanel.paidToDate') }}</p>
          <p class="mt-0.5 text-lg font-semibold text-success-600">{{ formatCurrency(budget.totalPaid, budget.currency) }}</p>
        </div>
        <div>
          <p class="text-xs text-text-secondary">{{ t('customer.budgetPanel.remaining') }}</p>
          <p class="mt-0.5 text-lg font-semibold text-text-primary">{{ formatCurrency(budget.totalDue, budget.currency) }}</p>
        </div>
      </div>

      <div class="h-2 overflow-hidden rounded-full bg-border-default">
        <div class="h-full rounded-full bg-success-500" :style="{ width: `${paidPercent}%` }" />
      </div>

      <div>
        <p class="mb-2 text-sm font-semibold text-text-primary">{{ t('customer.budgetPanel.upcomingPayments') }}</p>
        <EmptyState
          v-if="budget.upcomingPayments.length === 0"
          :title="t('customer.budgetPanel.nothingOutstandingTitle')"
          :description="t('customer.budgetPanel.nothingOutstandingDescription')"
        />
        <div v-else class="flex flex-col gap-2">
          <div
            v-for="payment in budget.upcomingPayments"
            :key="payment.description + payment.dueDate"
            class="flex items-center justify-between rounded-lg border p-3"
            :class="isPastDate(payment.dueDate) ? 'border-danger-200 bg-danger-50' : 'border-border-light bg-bg-card'"
          >
            <div>
              <p class="text-sm font-medium text-text-primary">{{ payment.description }}</p>
              <!-- Deliberately no due date shown to the customer here --
                   only whether it's overdue, not the schedule itself. -->
              <p v-if="isPastDate(payment.dueDate)" class="text-xs text-danger-600">{{ t('customer.budgetPanel.overdue') }}</p>
            </div>
            <div class="text-end">
              <p class="text-sm font-semibold text-text-primary">
                {{ formatCurrency(payment.amountDue - payment.amountReceived, budget.currency) }}
              </p>
              <p v-if="payment.amountReceived > 0" class="text-xs text-text-secondary">
                {{ t('customer.budgetPanel.received', { amount: formatCurrency(payment.amountReceived, budget.currency) }) }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>
