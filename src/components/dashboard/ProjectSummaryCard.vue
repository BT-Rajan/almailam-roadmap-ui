<script setup lang="ts">
import { computed } from 'vue'
import type { ProjectSummary } from '@/types/Dashboard'
import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

interface Props {
  project: ProjectSummary
}

const props = withDefaults(defineProps<Props>(), {})

defineEmits<{
  click: []
}>()


const progressColor = computed(() => {
  if (props.project.progress >= 75) return 'bg-success-500'
  if (props.project.progress >= 50) return 'bg-info-500'
  if (props.project.progress >= 25) return 'bg-warning-500'
  return 'bg-danger-500'
})

const statusVariant = computed(() => {
  const variants: Record<string, any> = {
    draft: 'neutral',
    active: 'info',
    pending: 'warning',
    completed: 'success',
    'on-hold': 'warning',
  }
  return variants[props.project.status] || 'neutral'
})
</script>

<template>
  <Card hoverable class="cursor-pointer space-y-3" @click="$emit('click')">
    <div class="flex items-start justify-between gap-2">
      <div class="flex-1 min-w-0">
        <h3 class="font-medium text-neutral-900 truncate">{{ project.name }}</h3>
        <p class="text-xs text-neutral-500 truncate">{{ project.client }}</p>
      </div>
      <StatusBadge :label="project.status" :variant="statusVariant" />
    </div>

    <div class="space-y-2">
      <div class="flex items-center justify-between text-xs">
        <span class="text-neutral-600">Progress</span>
        <span class="font-medium text-neutral-900">{{ project.progress }}%</span>
      </div>
      <div class="h-2 bg-neutral-100 rounded-full overflow-hidden">
        <div :class="['h-full transition-all duration-normal', progressColor]" :style="{ width: `${project.progress}%` }" />
      </div>
    </div>

    <div class="text-xs text-neutral-500">
      Due {{ new Date(project.dueDate).toLocaleDateString() }}
    </div>
  </Card>
</template>
