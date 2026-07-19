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

const formatDate = (date: string) =>
  new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
</script>

<template>
  <Card class="bg-white">
    <div class="space-y-6">
      <!-- Title and Status -->
      <div class="flex items-start justify-between gap-4">
        <div class="flex-1">
          <h1 class="text-3xl font-bold text-neutral-900">{{ project.projectName }}</h1>
          <p class="text-neutral-600 mt-2">{{ project.description }}</p>
          <p class="text-sm text-neutral-500 mt-3">
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
          <span class="text-sm font-medium text-neutral-700">Overall Progress</span>
          <span class="text-sm font-bold text-neutral-900">{{ project.progress }}%</span>
        </div>
        <div class="h-3 bg-neutral-100 rounded-full overflow-hidden">
          <div
            :class="['h-full transition-all duration-500', progressColor]"
            :style="{ width: `${project.progress}%` }"
          />
        </div>
      </div>

      <!-- Summary Text -->
      <div class="rounded-lg bg-neutral-50 border border-neutral-200 p-4">
        <p class="text-sm text-neutral-700">{{ project.summary }}</p>
      </div>

      <!-- Timeline Info -->
      <div class="grid grid-cols-1 tablet:grid-cols-3 gap-4">
        <div class="space-y-1">
          <p class="text-xs text-neutral-600 uppercase font-medium">Start Date</p>
          <p class="text-sm font-medium text-neutral-900">{{ formatDate(project.startDate) }}</p>
        </div>
        <div class="space-y-1">
          <p class="text-xs text-neutral-600 uppercase font-medium">Expected Completion</p>
          <p class="text-sm font-medium text-neutral-900">{{ formatDate(project.expectedEndDate) }}</p>
          <p v-if="daysRemaining > 0" class="text-xs text-neutral-500 mt-1">{{ daysRemaining }} days remaining</p>
          <p v-else class="text-xs text-danger-500 font-medium mt-1">Target date passed</p>
        </div>
        <div v-if="project.actualEndDate" class="space-y-1">
          <p class="text-xs text-neutral-600 uppercase font-medium">Actual Completion</p>
          <p class="text-sm font-medium text-success-600">{{ formatDate(project.actualEndDate) }}</p>
        </div>
      </div>
    </div>
  </Card>
</template>
