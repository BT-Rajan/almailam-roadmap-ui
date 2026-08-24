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

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

// See BaseButton.vue's identical guard: reading `disabled` here is
// synchronous, closing the gap where Vue hasn't yet painted the native
// `disabled` attribute after a consumer sets it true (e.g. a delete
// action mid-flight), which could otherwise let a fast second click
// through.
function handleClick(event: MouseEvent): void {
  if (props.disabled) return
  emit('click', event)
}

const variantClasses: Record<string, string> = {
  ghost: 'text-text-muted hover:bg-bg-hover hover:text-text-primary',
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
  'disabled:cursor-not-allowed disabled:text-text-muted disabled:hover:bg-transparent',
  'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500',
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
    @click="handleClick"
  >
    <component :is="icon" :class="iconSizeClasses[size]" />
  </button>
</template>
