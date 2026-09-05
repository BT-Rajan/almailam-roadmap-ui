<script setup lang="ts">
import { Bell, CheckCircle2, FileText, TrendingUp } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ProjectUpdate } from '@/types/CustomerPortal'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { formatRelativeDate } from '@/utils/dateFormatter'

interface Props {
  updates: ProjectUpdate[]
}

const props = defineProps<Props>()
const { t } = useI18n()

const sortedUpdates = computed(() => {
  return [...props.updates].sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()).slice(0, 8)
})

const getUpdateIcon = (type: string) => {
  if (type === 'milestone') return CheckCircle2
  if (type === 'deliverable') return FileText
  if (type === 'status') return TrendingUp
  return Bell
}

const getUpdateColor = (type: string) => {
  if (type === 'milestone') return 'bg-success-50 border-success-200'
  if (type === 'deliverable') return 'bg-info-50 border-info-200'
  if (type === 'status') return 'bg-warning-50 border-warning-200'
  return 'bg-bg-secondary border-border-default'
}

const getIconColor = (type: string) => {
  if (type === 'milestone') return 'text-success-600'
  if (type === 'deliverable') return 'text-info-600'
  if (type === 'status') return 'text-warning-600'
  return 'text-text-secondary'
}
</script>

<template>
  <Card>
    <template #header>
      <h2 class="text-xl font-semibold text-text-primary">{{ t('customer.updatesPanel.title') }}</h2>
    </template>

    <div v-if="sortedUpdates.length === 0">
      <EmptyState :icon="Bell" :title="t('customer.updatesPanel.emptyTitle')" :description="t('customer.updatesPanel.emptyDescription')" />
    </div>

    <div v-else class="space-y-3">
      <div v-for="update in sortedUpdates" :key="update.id" :class="['p-4 rounded-lg border', getUpdateColor(update.type)]">
        <div class="flex gap-3">
          <component :is="getUpdateIcon(update.type)" :class="['h-5 w-5 flex-shrink-0 mt-0.5', getIconColor(update.type)]" />
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-2">
              <div>
                <h3 class="font-medium text-text-primary">{{ update.title }}</h3>
                <p v-if="update.description" class="text-sm text-text-secondary mt-1">{{ update.description }}</p>
              </div>
              <span class="text-xs text-text-muted flex-shrink-0 mt-0.5">{{ formatRelativeDate(update.date) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>
