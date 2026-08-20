<script setup lang="ts">
import { Loader2 } from '@lucide/vue'
import { computed } from 'vue'
import type { Component } from 'vue'

import type { ButtonVariant, ComponentSize } from '@/types/Ui'

interface Props {
  variant?: ButtonVariant
  size?: ComponentSize
  type?: 'button' | 'submit'
  icon?: Component
  iconPosition?: 'left' | 'right'
  loading?: boolean
  disabled?: boolean
  fullWidth?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
  icon: undefined,
  iconPosition: 'left',
  loading: false,
  disabled: false,
  fullWidth: false,
})

defineEmits<{
  click: [event: MouseEvent]
}>()

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'gradient-luxe text-neutral-0 shadow-glass-sm hover:brightness-110 focus-visible:outline-accent-500 disabled:opacity-40 disabled:brightness-100',
  secondary:
    'bg-bg-card text-text-primary border border-border-default backdrop-blur-xl hover:bg-bg-hover disabled:text-text-muted',
  ghost: 'bg-transparent text-text-secondary hover:bg-bg-hover disabled:text-text-muted',
  danger:
    'bg-danger-500 text-neutral-0 hover:bg-danger-700 focus-visible:outline-danger-500 disabled:bg-danger-100',
}

const sizeClasses: Record<ComponentSize, string> = {
  sm: 'h-8 px-3 text-xs gap-1.5',
  md: 'h-10 px-4 text-sm gap-2',
  lg: 'h-12 px-6 text-base gap-2',
}

const isDisabled = computed(() => props.disabled || props.loading)

const buttonClasses = computed(() => [
  'inline-flex items-center justify-center',
  'font-medium rounded-lg',
  'transition-colors duration-fast',
  'disabled:cursor-not-allowed',
  'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2',
  variantClasses[props.variant],
  sizeClasses[props.size],
  props.fullWidth ? 'w-full' : '',
])
</script>

<template>
  <button :type="type" :class="buttonClasses" :disabled="isDisabled" @click="$emit('click', $event)">
    <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
    <component :is="icon" v-else-if="icon && iconPosition === 'left'" class="h-4 w-4" />
    <slot />
    <component :is="icon" v-if="!loading && icon && iconPosition === 'right'" class="h-4 w-4" />
  </button>
</template>
