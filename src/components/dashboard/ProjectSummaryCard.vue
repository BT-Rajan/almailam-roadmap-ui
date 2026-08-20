<script setup lang="ts">
import { computed } from 'vue'
import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ProjectSummary } from '@/types/Dashboard'
import type { BadgeVariant } from '@/types/Ui'

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

const statusVariant = computed<BadgeVariant>(() => {
  const variants: Record<string, BadgeVariant> = {
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
        <h3 class="font-medium text-text-primary truncate">{{ project.name }}</h3>
        <p class="text-xs text-text-muted truncate">{{ project.client }}</p>
      </div>
      <StatusBadge :label="project.status" :variant="statusVariant" />
    </div>

    <div class="space-y-2">
      <div class="flex items-center justify-between text-xs">
        <span class="text-text-secondary">Progress</span>
        <span class="font-medium text-text-primary">{{ project.progress }}%</span>
      </div>
      <div class="h-2 bg-bg-secondary rounded-full overflow-hidden">
        <div :class="['h-full transition-all duration-normal', progressColor]" :style="{ width: `${project.progress}%` }" />
      </div>
    </div>

    <div class="text-xs text-text-muted">
      Due {{ new Date(project.dueDate).toLocaleDateString() }}
    </div>
  </Card>
</template>
