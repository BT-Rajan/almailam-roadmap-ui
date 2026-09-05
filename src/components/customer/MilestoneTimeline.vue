<script setup lang="ts">
import { CheckCircle2, Clock, AlertCircle } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ProjectMilestone } from '@/types/CustomerPortal'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { isPastDate } from '@/utils/dateFormatter'

interface Props {
  milestones: ProjectMilestone[]
}

const props = defineProps<Props>()
const { t } = useI18n()

const MILESTONE_STATUS_KEYS: Record<string, string> = {
  completed: 'customer.milestoneStatus.completed',
  'in-progress': 'customer.milestoneStatus.inProgress',
  delayed: 'customer.milestoneStatus.delayed',
  upcoming: 'customer.milestoneStatus.upcoming',
}

function milestoneStatusLabel(status: string): string {
  return t(MILESTONE_STATUS_KEYS[status] ?? 'customer.milestoneStatus.upcoming')
}

const sortedMilestones = computed(() => {
  return [...props.milestones].sort((a, b) => new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime())
})

const getStatusIcon = (status: string) => {
  if (status === 'completed') return CheckCircle2
  if (status === 'delayed') return AlertCircle
  return Clock
}

const getStatusColor = (status: string) => {
  if (status === 'completed') return 'text-success-500'
  if (status === 'delayed') return 'text-danger-500'
  if (status === 'in-progress') return 'text-info-500'
  return 'text-text-muted'
}

const formatDate = (date: string) =>
  new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

const isOverdue = (dueDate: string, status: string) => {
  // Server already renders "delayed" as its own status pill for the
  // common case (an "upcoming" milestone past its due date) -- only add
  // this separate "Overdue" flag for the case that status doesn't cover:
  // an "in-progress" milestone whose due date has since passed. Showing
  // both for the same milestone would just be the same warning twice.
  // isPastDate compares calendar dates, not instants -- a plain
  // `new Date(dueDate) < new Date()` would flag anything due "today"
  // as already overdue the moment the clock ticks past UTC midnight.
  return status !== 'completed' && status !== 'delayed' && isPastDate(dueDate)
}
</script>

<template>
  <Card>
    <template #header>
      <h2 class="text-xl font-semibold text-text-primary">{{ t('customer.milestoneTimeline.title') }}</h2>
    </template>

    <div v-if="sortedMilestones.length === 0">
      <EmptyState :icon="Clock" :title="t('customer.milestoneTimeline.emptyTitle')" :description="t('customer.milestoneTimeline.emptyDescription')" />
    </div>

    <div v-else class="space-y-6">
      <div v-for="(milestone, index) in sortedMilestones" :key="milestone.id" class="flex gap-4">
        <!-- Timeline Line and Icon -->
        <div class="flex flex-col items-center gap-2">
          <component :is="getStatusIcon(milestone.status)" :class="['h-6 w-6', getStatusColor(milestone.status)]" />
          <div v-if="index < sortedMilestones.length - 1" class="h-12 w-0.5 bg-border-default" />
        </div>

        <!-- Milestone Info -->
        <div class="flex-1 pb-4">
          <div class="space-y-2">
            <div class="flex items-start justify-between gap-2">
              <div>
                <h3 class="font-semibold text-text-primary">{{ milestone.title }}</h3>
                <p v-if="milestone.description" class="text-sm text-text-secondary mt-1">{{ milestone.description }}</p>
              </div>
              <span
                :class="[
                  'text-xs font-medium px-2.5 py-1 rounded-full flex-shrink-0',
                  milestone.status === 'completed'
                    ? 'bg-success-100 text-success-700'
                    : milestone.status === 'in-progress'
                      ? 'bg-info-100 text-info-700'
                      : milestone.status === 'delayed'
                        ? 'bg-danger-100 text-danger-700'
                        : 'bg-bg-secondary text-text-secondary',
                ]"
              >
                {{ milestoneStatusLabel(milestone.status) }}
              </span>
            </div>

            <!-- Dates -->
            <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-text-secondary">
              <span>{{ t('customer.milestoneTimeline.due') }} <strong>{{ formatDate(milestone.dueDate) }}</strong></span>
              <span v-if="milestone.completedDate" class="text-success-600">
                {{ t('customer.milestoneTimeline.completed') }} <strong>{{ formatDate(milestone.completedDate) }}</strong>
              </span>
              <span v-if="isOverdue(milestone.dueDate, milestone.status)" class="text-danger-600 font-medium">
                ⚠ {{ t('customer.milestoneTimeline.overdue') }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>
