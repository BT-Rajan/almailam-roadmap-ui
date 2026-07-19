<script setup lang="ts">
import { FileSignature } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
import { getContractStatusVariant } from '@/utils/contractHelpers'
import type { Contract } from '@/types/Contract'

interface Props {
  contracts: Contract[]
  selectedContractId?: string
}

withDefaults(defineProps<Props>(), {
  selectedContractId: undefined,
})

const emit = defineEmits<{
  select: [contractId: string]
}>()
</script>

<template>
  <Card :padded="false">
    <template #header>
      <h3 class="text-sm font-semibold text-neutral-800">Contracts</h3>
    </template>

    <EmptyState
      v-if="contracts.length === 0"
      :icon="FileSignature"
      title="No contracts yet"
      description="Contracts issued for this project will appear here."
    />

    <ul v-else class="divide-y divide-border-light">
      <li v-for="contract in [...contracts].reverse()" :key="contract.id">
        <button
          type="button"
          class="flex w-full flex-col gap-1.5 px-5 py-4 text-left transition-colors duration-fast"
          :class="contract.id === selectedContractId ? 'bg-bg-selected' : 'hover:bg-bg-hover'"
          @click="emit('select', contract.id)"
        >
          <div class="flex items-center justify-between gap-3">
            <span class="text-sm font-semibold text-neutral-800">{{ contract.contractNo }}</span>
            <StatusBadge
              :label="contract.status"
              :variant="getContractStatusVariant(contract.status)"
              size="sm"
            />
          </div>
          <p class="text-xs text-neutral-500">
            Revision {{ contract.revision }} · Issued {{ formatDate(contract.issueDate) }}
          </p>
          <p class="truncate text-xs text-neutral-400">{{ contract.templateName }}</p>
          <p class="text-sm font-medium text-neutral-700">
            {{ formatCurrency(contract.contractValue, contract.currency) }}
          </p>
        </button>
      </li>
    </ul>
  </Card>
</template>
