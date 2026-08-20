<script setup lang="ts">
import { computed } from 'vue'
import type { CustomerProjectStatus } from '@/types/CustomerPortal'
import type { BadgeVariant } from '@/types/Ui'
import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

interface Props {
  project: CustomerProjectStatus
}

const props = defineProps<Props>()

const statusVariant = computed(() => {
  const variants: Record<string, BadgeVariant> = {
    planning: 'warning',
    active: 'info',
    'on-hold': 'warning',
    completed: 'success',
    cancelled: 'danger',
  }
  return variants[props.project.status] || 'neutral'
})

const progressColor = computed(() => {
  if (props.project.progress >= 75) return 'bg-success-500'
  if (props.project.progress >= 50) return 'bg-info-500'
  if (props.project.progress >= 25) return 'bg-warning-500'
  return 'bg-danger-500'
})

const daysRemaining = computed(() => {
  const today = new Date()
  const endDate = new Date(props.project.expectedEndDate)
  const diff = Math.ceil((endDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
  return diff
})

// A completed (or cancelled) project's target date is history, not a
// live concern -- "days remaining" / "Target date passed" only make
// sense while something is still actively in progress. The Actual
// Completion block below already covers what matters once it's done.
const isActiveTimeline = computed(() => props.project.status !== 'completed' && props.project.status !== 'cancelled')
const showOverdueWarning = computed(() => isActiveTimeline.value && daysRemaining.value <= 0)

const formatDate = (date: string) =>
  new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
</script>

<template>
  <Card>
    <div class="space-y-6">
      <!-- Title and Status -->
      <div class="flex flex-col gap-4 tablet:flex-row tablet:items-start tablet:justify-between">
        <div class="flex-1">
          <h1 class="text-xl font-bold text-text-primary tablet:text-3xl">{{ project.projectName }}</h1>
          <p class="text-text-secondary mt-2">{{ project.description }}</p>
          <p class="text-sm text-text-muted mt-3">
            <strong>Client:</strong> {{ project.clientName }}
          </p>
        </div>
        <div class="flex-shrink-0">
          <StatusBadge :label="project.status" :variant="statusVariant" />
        </div>
      </div>

      <!-- Progress Bar -->
      <div class="space-y-2">
        <div class="flex items-center justify-between">
          <span class="text-sm font-medium text-text-secondary">Overall Progress</span>
          <span class="text-sm font-bold text-text-primary">{{ project.progress }}%</span>
        </div>
        <div class="h-3 bg-bg-secondary rounded-full overflow-hidden">
          <div
            :class="['h-full transition-all duration-500', progressColor]"
            :style="{ width: `${project.progress}%` }"
          />
        </div>
      </div>

      <!-- Summary Text -->
      <div class="rounded-lg bg-bg-secondary border border-border-default p-4">
        <p class="text-sm text-text-secondary">{{ project.summary }}</p>
      </div>

      <!-- Timeline Info -->
      <div class="grid grid-cols-1 tablet:grid-cols-3 gap-4">
        <div class="space-y-1">
          <p class="text-xs text-text-secondary uppercase font-medium">Start Date</p>
          <p class="text-sm font-medium text-text-primary">{{ formatDate(project.startDate) }}</p>
        </div>
        <div class="space-y-1">
          <p class="text-xs text-text-secondary uppercase font-medium">Expected Completion</p>
          <p class="text-sm font-medium text-text-primary">{{ formatDate(project.expectedEndDate) }}</p>
          <p v-if="isActiveTimeline && !showOverdueWarning" class="text-xs text-text-muted mt-1">{{ daysRemaining }} days remaining</p>
          <p v-else-if="showOverdueWarning" class="text-xs text-danger-500 font-medium mt-1">Target date passed</p>
        </div>
        <div v-if="project.actualEndDate" class="space-y-1">
          <p class="text-xs text-text-secondary uppercase font-medium">Actual Completion</p>
          <p class="text-sm font-medium text-success-600">{{ formatDate(project.actualEndDate) }}</p>
        </div>
      </div>
    </div>
  </Card>
</template>
