<script setup lang="ts">
import { computed } from 'vue'
import type { StatisticItem } from '@/types/Dashboard'
import Card from '@/components/common/Card.vue'

interface Props {
  statistic: StatisticItem
}

const props = withDefaults(defineProps<Props>(), {})

defineEmits<{
  click: []
}>()


const bgColor = computed(() => {
  const colors: Record<string, string> = {
    primary: 'bg-primary-50',
    success: 'bg-success-50',
    warning: 'bg-warning-50',
    danger: 'bg-danger-50',
    info: 'bg-info-50',
  }
  return colors[props.statistic.color || 'primary']
})

const textColor = computed(() => {
  const colors: Record<string, string> = {
    primary: 'text-primary-600',
    success: 'text-success-600',
    warning: 'text-warning-600',
    danger: 'text-danger-600',
    info: 'text-info-600',
  }
  return colors[props.statistic.color || 'primary']
})
</script>

<template>
  <Card hoverable class="cursor-pointer" @click="$emit('click')">
    <div class="flex flex-col gap-3">
      <div v-if="statistic.icon" :class="['flex h-11 w-11 items-center justify-center rounded-2xl', bgColor]">
        <component :is="statistic.icon" :class="['h-5 w-5', textColor]" />
      </div>
      <div>
        <p class="text-2xl font-bold leading-tight text-text-primary">{{ statistic.value }}</p>
        <p class="mt-1 text-xs font-medium text-text-muted">{{ statistic.label }}</p>
      </div>
    </div>
  </Card>
</template>
