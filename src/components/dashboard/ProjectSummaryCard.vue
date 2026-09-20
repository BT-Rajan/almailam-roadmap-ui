<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ProjectSummary } from '@/types/Dashboard'
import type { BadgeVariant } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'

interface Props {
  project: ProjectSummary
}

const props = withDefaults(defineProps<Props>(), {})
const { t } = useI18n()

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

const statusLabelKeys: Record<string, string> = {
  draft: 'dashboard.projectStatus.draft',
  active: 'dashboard.projectStatus.active',
  pending: 'dashboard.projectStatus.pending',
  completed: 'dashboard.projectStatus.completed',
  'on-hold': 'dashboard.projectStatus.onHold',
}

const statusLabel = computed(() => {
  const key = statusLabelKeys[props.project.status]
  return key ? t(key) : props.project.status
})
const initials = computed(() =>
  props.project.name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase())
    .join(''),
)
</script>

<template>
  <Card hoverable class="cursor-pointer" @click="$emit('click')">
    <div class="flex flex-col gap-3">
      <div class="flex items-start gap-3">
        <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent-50 text-sm font-semibold text-accent-700">
          {{ initials }}
        </span>
        <div class="min-w-0 flex-1">
          <h3 class="truncate font-medium text-text-primary">{{ project.name }}</h3>
          <p class="truncate text-xs text-text-muted">{{ project.client }}</p>
        </div>
        <StatusBadge :label="statusLabel" :variant="statusVariant" class="shrink-0" />
      </div>

      <div class="space-y-2">
        <div class="flex items-center justify-between text-xs">
          <span class="text-text-secondary">{{ t('dashboard.progress') }}</span>
          <span class="font-medium text-text-primary">{{ project.progress }}%</span>
        </div>
        <div class="h-2 bg-bg-secondary rounded-full overflow-hidden">
          <div :class="['h-full transition-all duration-normal', progressColor]" :style="{ width: `${project.progress}%` }" />
        </div>
      </div>

      <div class="text-xs text-text-muted">
        {{ t('dashboard.due', { date: formatDate(project.dueDate) }) }}
      </div>
    </div>
  </Card>
</template>
