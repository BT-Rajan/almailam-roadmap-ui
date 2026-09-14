<script setup lang="ts">
import { AlertTriangle } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Card from '@/components/common/Card.vue'
import type { OverdueAgreement } from '@/types/Dashboard'
import { formatCurrency } from '@/utils/currencyFormatter'

interface Props {
  agreements: OverdueAgreement[]
  title?: string
  maxItems?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: undefined,
  maxItems: 6,
})

const { t } = useI18n()

defineEmits<{
  'agreement-click': [projectId: string]
}>()

// Worst-affected agreements first -- what a reader here actually needs
// is "who to chase," not an arbitrary or creation-order list.
const displayedAgreements = computed(() =>
  [...props.agreements].sort((a, b) => b.overdueAmount - a.overdueAmount).slice(0, props.maxItems),
)
</script>

<template>
  <Card>
    <template #header>
      <h3 class="font-medium text-text-primary">{{ title ?? t('dashboard.overdueAgreements') }}</h3>
    </template>

    <div v-if="displayedAgreements.length === 0" class="py-8 text-center text-text-muted">
      <p class="text-sm">{{ t('dashboard.noOverdueAgreements') }}</p>
    </div>
    <div v-else class="space-y-2">
      <div
        v-for="agreement in displayedAgreements"
        :key="agreement.id"
        class="p-3 rounded-lg border border-border-light hover:bg-bg-hover transition-colors cursor-pointer flex items-start gap-3"
        @click="$emit('agreement-click', agreement.projectId)"
      >
        <AlertTriangle class="h-5 w-5 text-danger-500 flex-shrink-0 mt-0.5" />
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-text-primary truncate">{{ agreement.project }}</p>
          <p class="text-xs text-text-muted mt-1">{{ agreement.client }}</p>
        </div>
        <span class="text-sm font-medium text-danger-600 flex-shrink-0">
          {{ formatCurrency(agreement.overdueAmount, agreement.currency) }}
        </span>
      </div>
    </div>
  </Card>
</template>
