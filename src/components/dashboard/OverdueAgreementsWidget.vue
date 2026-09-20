<script setup lang="ts">
import { AlertTriangle, ChevronLeft, ChevronRight } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useLocale } from '@/composables/useLocale'
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
const { isRtl } = useLocale()
const chevronIcon = computed(() => (isRtl.value ? ChevronLeft : ChevronRight))

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
  <Card :padded="false">
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ title ?? t('dashboard.overdueAgreements') }}</h3>
    </template>

    <EmptyState v-if="displayedAgreements.length === 0" :title="t('dashboard.noOverdueAgreements')" :bordered="false" />
    <ul v-else class="divide-y divide-border-light">
      <li
        v-for="agreement in displayedAgreements"
        :key="agreement.id"
        class="flex cursor-pointer items-center gap-3 px-5 py-3.5 transition-colors hover:bg-bg-hover"
        @click="$emit('agreement-click', agreement.projectId)"
      >
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-danger-50">
          <AlertTriangle class="h-5 w-5 text-danger-500" />
        </span>
        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-medium text-text-primary">{{ agreement.project }}</p>
          <p class="mt-0.5 truncate text-xs text-text-muted">{{ agreement.client }}</p>
        </div>
        <span class="shrink-0 text-sm font-semibold text-danger-600">
          {{ formatCurrency(agreement.overdueAmount, agreement.currency) }}
        </span>
        <component :is="chevronIcon" class="h-4 w-4 shrink-0 text-text-muted" />
      </li>
    </ul>
  </Card>
</template>
