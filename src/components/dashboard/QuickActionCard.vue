<script setup lang="ts">
import { computed, type Component } from 'vue'
import Card from '@/components/common/Card.vue'

interface Props {
  label: string
  icon: Component
  description?: string
  color?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  description: undefined,
  color: 'primary',
  disabled: false,
})

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
  return colors[props.color || 'primary']
})

const iconColor = computed(() => {
  const colors: Record<string, string> = {
    primary: 'text-primary-600',
    success: 'text-success-600',
    warning: 'text-warning-600',
    danger: 'text-danger-600',
    info: 'text-info-600',
  }
  return colors[props.color || 'primary']
})
</script>

<template>
  <Card hoverable class="cursor-pointer" :class="disabled ? 'opacity-50 cursor-not-allowed' : ''" @click="!disabled && $emit('click')">
    <div class="text-center space-y-3">
      <div :class="['w-12 h-12 rounded-lg flex items-center justify-center mx-auto', bgColor]">
        <component :is="icon" :class="['h-6 w-6', iconColor]" />
      </div>
      <div>
        <p class="font-medium text-neutral-900">{{ label }}</p>
        <p v-if="description" class="text-xs text-neutral-500 mt-1">{{ description }}</p>
      </div>
    </div>
  </Card>
</template>
