<script setup lang="ts">
import { computed } from 'vue'
import type { Component } from 'vue'

import type { ComponentSize } from '@/types/Ui'

interface Props {
  icon: Component
  label: string
  variant?: 'ghost' | 'primary' | 'danger'
  size?: ComponentSize
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'ghost',
  size: 'md',
  disabled: false,
})

defineEmits<{
  click: [event: MouseEvent]
}>()

const variantClasses: Record<string, string> = {
  ghost: 'text-neutral-500 hover:bg-bg-hover hover:text-neutral-800',
  primary: 'text-primary-600 hover:bg-primary-50',
  danger: 'text-danger-500 hover:bg-danger-50',
}

const sizeClasses: Record<ComponentSize, string> = {
  sm: 'h-8 w-8',
  md: 'h-10 w-10',
  lg: 'h-12 w-12',
}

const iconSizeClasses: Record<ComponentSize, string> = {
  sm: 'h-4 w-4',
  md: 'h-5 w-5',
  lg: 'h-6 w-6',
}

const buttonClasses = computed(() => [
  'inline-flex items-center justify-center',
  'rounded-lg transition-colors duration-fast',
  'disabled:cursor-not-allowed disabled:text-neutral-300 disabled:hover:bg-transparent',
  'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-500',
  variantClasses[props.variant],
  sizeClasses[props.size],
])
</script>

<template>
  <button
    type="button"
    :class="buttonClasses"
    :disabled="disabled"
    :aria-label="label"
    :title="label"
    @click="$emit('click', $event)"
  >
    <component :is="icon" :class="iconSizeClasses[size]" />
  </button>
</template>
