<script setup lang="ts">
import { CalendarClock, ChevronLeft, ChevronRight } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Deadline } from '@/types/Dashboard'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PaginatedList from '@/components/common/PaginatedList.vue'
import { useLocale } from '@/composables/useLocale'

interface Props {
  deadlines: Deadline[]
  title?: string
  pageSize?: number
  emptyText?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: undefined,
  pageSize: 5,
  emptyText: undefined,
})

const { t } = useI18n()
const { isRtl } = useLocale()
const chevronIcon = computed(() => (isRtl.value ? ChevronLeft : ChevronRight))

defineEmits<{
  'deadline-click': [deadlineId: string]
}>()


const sortedDeadlines = computed(() =>
  [...props.deadlines]
    .sort((a, b) => new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime())
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

// The icon badge's own colors -- a stronger, more "flagged" visual than
// the text-only status label used to give on its own, same intent as
// the colored icon badges every stat tile (StatisticsCard) already uses.
const badgeColor = (status: string) => {
  const colors: Record<string, string> = {
    overdue: 'bg-danger-50 text-danger-600',
    today: 'bg-warning-50 text-warning-600',
    urgent: 'bg-warning-50 text-warning-600',
    soon: 'bg-info-50 text-info-600',
    upcoming: 'bg-bg-secondary text-text-muted',
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
  <Card :padded="false">
    <template #header>
      <h3 class="text-center text-sm font-semibold text-text-primary">{{ title ?? t('dashboard.upcomingDeadlines') }}</h3>
    </template>

    <EmptyState v-if="sortedDeadlines.length === 0" :title="emptyText ?? t('dashboard.noUpcomingDeadlines')" :bordered="false" />
    <PaginatedList v-else :items="sortedDeadlines" :page-size="pageSize" pager-inset="card">
      <template #default="{ items }">
        <ul class="divide-y divide-border-light">
          <li
            v-for="deadline in items"
            :key="deadline.id"
            class="flex cursor-pointer items-center gap-3 px-5 py-3.5 transition-colors hover:bg-bg-hover"
            @click="$emit('deadline-click', deadline.id)"
          >
            <span :class="['flex h-10 w-10 shrink-0 items-center justify-center rounded-full', badgeColor(deadlineStatus(daysUntilDeadline(deadline.dueDate)))]">
              <CalendarClock class="h-5 w-5" />
            </span>
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-text-primary">{{ deadline.title }}</p>
              <p class="mt-0.5 truncate text-xs text-text-muted">{{ deadline.project }}</p>
            </div>
            <span :class="['shrink-0 text-xs font-semibold', statusTextColor(deadlineStatus(daysUntilDeadline(deadline.dueDate)))]">
              {{ statusLabel(deadlineStatus(daysUntilDeadline(deadline.dueDate)), daysUntilDeadline(deadline.dueDate)) }}
            </span>
            <component :is="chevronIcon" class="h-4 w-4 shrink-0 text-text-muted" />
          </li>
        </ul>
      </template>
    </PaginatedList>
  </Card>
</template>
