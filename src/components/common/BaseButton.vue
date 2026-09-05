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

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

// Guards the emit itself, not just the native `disabled` attribute --
// Vue applies a reactive prop change (loading/disabled going true) to
// the DOM asynchronously (its own render scheduler), so a fast
// double-click or an impatient second click while an async action is
// already running can otherwise fire a second `click` before the
// button visually disables. Reading `isDisabled` here is synchronous
// and reflects the current prop value immediately, closing that gap
// for every consumer of this component at once -- this is what a
// double-submit anywhere in the app (see NewProjectWizardPage.vue's
// duplicate-project bug) actually needs guarded against, not just the
// page-level handler.
function handleClick(event: MouseEvent): void {
  if (isDisabled.value) return
  emit('click', event)
}

const variantClasses: Record<ButtonVariant, string> = {
  // Every default-variant button in the app (New Project, Sign In, Save,
  // Submit, ...) renders through this one variant -- it needs to be the
  // brand's actual accent color, not graphite, or the app reads as two
  // competing identities: jade everywhere the brand shows through
  // deliberately (links, focus rings, the sidebar/login mark), graphite
  // everywhere a button defaults. JDK doesn't have this split -- its
  // primary CTA is the same gold as everything else -- which is why it
  // reads as one uniform product instead of patchwork.
  primary:
    'gradient-luxe-accent text-neutral-0 shadow-glass-sm hover:brightness-110 focus-visible:outline-accent-500 disabled:opacity-40 disabled:brightness-100',
  secondary:
    // No backdrop-blur here, deliberately -- FilterBar, SelectBox,
    // TextInput, Card, and every other bg-bg-card surface in the app
    // (16 components) use this exact token as a flat translucent tint
    // with no blur. This button was the one place still adding
    // backdrop-blur-xl on top of it. A blurred surface samples whatever
    // sits behind it, so the SAME token+button rendered near the
    // ambient background's glow blobs picked up a visibly lighter,
    // washed-out tint than a plain dropdown two inches to its right
    // using the identical bg-bg-card color without blur -- position-
    // dependent inconsistency for what's supposed to be one shared
    // "glass surface" look, which is exactly what read as patchy.
    // (Modal panels via .glass-panel are a different, legitimately
    // blurred tier -- floating overlays over blurred page content --
    // not inline page furniture like this.)
    'bg-bg-card text-text-primary border border-border-default hover:bg-bg-hover disabled:text-text-muted',
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
  <button :type="type" :class="buttonClasses" :disabled="isDisabled" @click="handleClick">
    <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
    <component :is="icon" v-else-if="icon && iconPosition === 'left'" class="h-4 w-4" />
    <slot />
    <component :is="icon" v-if="!loading && icon && iconPosition === 'right'" class="h-4 w-4" />
  </button>
</template>
