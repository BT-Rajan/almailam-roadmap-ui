<script setup lang="ts">
import { FileSignature } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

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

const { t } = useI18n()

const CONTRACT_STATUS_KEYS: Record<Contract['status'], string> = {
  Draft: 'project.contractStatus.draft',
  Signed: 'project.contractStatus.signed',
  Active: 'project.contractStatus.active',
  Expired: 'project.contractStatus.expired',
  Terminated: 'project.contractStatus.terminated',
}
</script>

<template>
  <Card :padded="false">
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('project.contractList.title') }}</h3>
    </template>

    <EmptyState
      v-if="contracts.length === 0"
      :icon="FileSignature"
      :title="t('project.contractList.emptyTitle')"
      :description="t('project.contractList.emptyDescription')"
    />

    <ul v-else class="divide-y divide-border-light">
      <li v-for="contract in [...contracts].reverse()" :key="contract.id">
        <button
          type="button"
          class="flex w-full flex-col gap-1.5 px-5 py-4 text-start transition-colors duration-fast"
          :class="contract.id === selectedContractId ? 'bg-bg-selected' : 'hover:bg-bg-hover'"
          :aria-current="contract.id === selectedContractId ? 'true' : undefined"
          @click="emit('select', contract.id)"
        >
          <div class="flex items-center justify-between gap-3">
            <span class="text-sm font-semibold text-text-primary">{{ contract.contractNo }}</span>
            <StatusBadge
              :label="t(CONTRACT_STATUS_KEYS[contract.status])"
              :variant="getContractStatusVariant(contract.status)"
              size="sm"
            />
          </div>
          <p class="text-xs text-text-muted">
            {{ t('project.contractList.revisionIssued', { revision: contract.revision, date: formatDate(contract.issueDate) }) }}
          </p>
          <p class="text-sm font-medium text-text-secondary">
            {{ formatCurrency(contract.contractValue, contract.currency) }}
          </p>
        </button>
      </li>
    </ul>
  </Card>
</template>
