<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Deadline } from '@/types/Dashboard'
import Card from '@/components/common/Card.vue'

interface Props {
  deadlines: Deadline[]
  title?: string
  maxItems?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: undefined,
  maxItems: 5,
})

const { t } = useI18n()

defineEmits<{
  'deadline-click': [deadlineId: string]
}>()


const sortedDeadlines = computed(() =>
  [...props.deadlines]
    .sort((a, b) => new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime())
    .slice(0, props.maxItems)
)

const daysUntilDeadline = (date: string) => {
  const now = new Date()
  const deadline = new Date(date)
  const diff = Math.ceil((deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
  return diff
}

const deadlineStatus = (days: number) => {
  if (days < 0) return 'overdue'
  if (days === 0) return 'today'
  if (days <= 3) return 'urgent'
  if (days <= 7) return 'soon'
  return 'upcoming'
}

const statusColor = (status: string) => {
  const colors: Record<string, string> = {
    overdue: 'bg-danger-50 border-danger-200',
    today: 'bg-warning-50 border-warning-200',
    urgent: 'bg-warning-50 border-warning-200',
    soon: 'bg-info-50 border-info-200',
    upcoming: 'bg-bg-secondary border-border-default',
  }
  return colors[status]
}

const statusTextColor = (status: string) => {
  const colors: Record<string, string> = {
    overdue: 'text-danger-600',
    today: 'text-warning-600',
    urgent: 'text-warning-600',
    soon: 'text-info-600',
    upcoming: 'text-text-secondary',
  }
  return colors[status]
}

const statusLabel = (status: string, days: number) => {
  if (status === 'overdue') return t('dashboard.deadlineOverdue', { days: Math.abs(days) })
  if (status === 'today') return t('dashboard.deadlineDueToday')
  return days === 1 ? t('dashboard.deadlineOneDayLeft') : t('dashboard.deadlineDaysLeft', { days })
}
</script>

<template>
  <Card>
    <template #header>
      <h3 class="font-medium text-text-primary">{{ title ?? t('dashboard.upcomingDeadlines') }}</h3>
    </template>

    <div v-if="sortedDeadlines.length === 0" class="py-8 text-center text-text-muted">
      <p class="text-sm">{{ t('dashboard.noUpcomingDeadlines') }}</p>
    </div>
    <div v-else class="space-y-2">
      <div
        v-for="deadline in sortedDeadlines"
        :key="deadline.id"
        :class="['p-3 rounded-lg border transition-colors cursor-pointer', statusColor(deadlineStatus(daysUntilDeadline(deadline.dueDate)))]"
        @click="$emit('deadline-click', deadline.id)"
      >
        <div class="flex items-start justify-between gap-2">
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-text-primary">{{ deadline.title }}</p>
            <p class="text-xs text-text-muted mt-1">{{ deadline.project }}</p>
          </div>
          <span :class="['text-xs font-medium flex-shrink-0', statusTextColor(deadlineStatus(daysUntilDeadline(deadline.dueDate)))]">
            {{ statusLabel(deadlineStatus(daysUntilDeadline(deadline.dueDate)), daysUntilDeadline(deadline.dueDate)) }}
          </span>
        </div>
      </div>
    </div>
  </Card>
</template>
