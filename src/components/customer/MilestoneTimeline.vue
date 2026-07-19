<script setup lang="ts">
import { CheckCircle2, Clock, AlertCircle } from '@lucide/vue'
import { computed } from 'vue'
import type { ProjectMilestone } from '@/types/CustomerPortal'
import Card from '@/components/common/Card.vue'

interface Props {
  milestones: ProjectMilestone[]
}

const props = defineProps<Props>()

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
  return 'text-neutral-400'
}

const formatDate = (date: string) =>
  new Date(date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })

const isOverdue = (dueDate: string, status: string) => {
  return status !== 'completed' && new Date(dueDate) < new Date()
}
</script>

<template>
  <Card>
    <template #header>
      <h2 class="text-xl font-semibold text-neutral-900">Project Milestones</h2>
    </template>

    <div v-if="sortedMilestones.length === 0" class="py-8 text-center text-neutral-500">
      <p>No milestones defined</p>
    </div>

    <div v-else class="space-y-6">
      <div v-for="(milestone, index) in sortedMilestones" :key="milestone.id" class="flex gap-4">
        <!-- Timeline Line and Icon -->
        <div class="flex flex-col items-center gap-2">
          <component :is="getStatusIcon(milestone.status)" :class="['h-6 w-6', getStatusColor(milestone.status)]" />
          <div v-if="index < sortedMilestones.length - 1" class="h-12 w-0.5 bg-neutral-200" />
        </div>

        <!-- Milestone Info -->
        <div class="flex-1 pb-4">
          <div class="space-y-2">
            <div class="flex items-start justify-between gap-2">
              <div>
                <h3 class="font-semibold text-neutral-900">{{ milestone.title }}</h3>
                <p v-if="milestone.description" class="text-sm text-neutral-600 mt-1">{{ milestone.description }}</p>
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
                        : 'bg-neutral-100 text-neutral-700',
                ]"
              >
                {{ milestone.status }}
              </span>
            </div>

            <!-- Dates -->
            <div class="flex items-center gap-4 text-sm text-neutral-600">
              <span>Due: <strong>{{ formatDate(milestone.dueDate) }}</strong></span>
              <span v-if="milestone.completedDate" class="text-success-600">
                Completed: <strong>{{ formatDate(milestone.completedDate) }}</strong>
              </span>
              <span v-if="isOverdue(milestone.dueDate, milestone.status)" class="text-danger-600 font-medium">
                ⚠ Overdue
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>
