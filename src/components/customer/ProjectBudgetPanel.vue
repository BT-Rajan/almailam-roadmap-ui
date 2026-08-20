<script setup lang="ts">
import { Wallet } from '@lucide/vue'
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { ProjectBudget } from '@/types/CustomerPortal'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'

const props = defineProps<{
  budget: ProjectBudget | null
}>()

const paidPercent = computed(() => {
  if (!props.budget || props.budget.contractAmount <= 0) return 0
  return Math.min(100, Math.round((props.budget.totalPaid / props.budget.contractAmount) * 100))
})

function isOverdue(dueDate: string): boolean {
  return new Date(dueDate) < new Date(new Date().toDateString())
}
</script>

<template>
  <Card>
    <template #header>
      <h2 class="text-xl font-semibold text-neutral-900">Budget & Payments</h2>
    </template>

    <EmptyState
      v-if="!budget"
      :icon="Wallet"
      title="No financial agreement on file"
      description="Contract and payment details will appear here once set up."
    />

    <div v-else class="flex flex-col gap-5">
      <div class="grid grid-cols-2 gap-4 tablet:grid-cols-3">
        <div>
          <p class="text-xs text-neutral-500">Contract Amount</p>
          <p class="mt-0.5 text-lg font-semibold text-neutral-900">{{ formatCurrency(budget.contractAmount, budget.currency) }}</p>
        </div>
        <div>
          <p class="text-xs text-neutral-500">Paid to Date</p>
          <p class="mt-0.5 text-lg font-semibold text-success-600">{{ formatCurrency(budget.totalPaid, budget.currency) }}</p>
        </div>
        <div>
          <p class="text-xs text-neutral-500">Remaining</p>
          <p class="mt-0.5 text-lg font-semibold text-neutral-900">{{ formatCurrency(budget.totalDue, budget.currency) }}</p>
        </div>
      </div>

      <div class="h-2 overflow-hidden rounded-full bg-neutral-200">
        <div class="h-full rounded-full bg-success-500" :style="{ width: `${paidPercent}%` }" />
      </div>

      <div>
        <p class="mb-2 text-sm font-semibold text-neutral-800">Upcoming Payments</p>
        <EmptyState
          v-if="budget.upcomingPayments.length === 0"
          title="Nothing outstanding"
          description="All scheduled payments have been settled."
        />
        <div v-else class="flex flex-col gap-2">
          <div
            v-for="payment in budget.upcomingPayments"
            :key="payment.description + payment.dueDate"
            class="flex items-center justify-between rounded-lg border p-3"
            :class="isOverdue(payment.dueDate) ? 'border-danger-200 bg-danger-50' : 'border-border-light bg-bg-card'"
          >
            <div>
              <p class="text-sm font-medium text-neutral-800">{{ payment.description }}</p>
              <p class="text-xs" :class="isOverdue(payment.dueDate) ? 'text-danger-600' : 'text-neutral-500'">
                Due {{ formatDate(payment.dueDate) }}
                <span v-if="isOverdue(payment.dueDate)">· Overdue</span>
              </p>
            </div>
            <div class="text-right">
              <p class="text-sm font-semibold text-neutral-800">
                {{ formatCurrency(payment.amountDue - payment.amountReceived, budget.currency) }}
              </p>
              <p v-if="payment.amountReceived > 0" class="text-xs text-neutral-500">
                {{ formatCurrency(payment.amountReceived, budget.currency) }} received
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>
