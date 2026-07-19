<script setup lang="ts">
import { AlertTriangle, CheckCircle2, Info, X, XCircle } from '@lucide/vue'
import { computed } from 'vue'
import type { Component } from 'vue'

import type { ToastVariant } from '@/types/Toast'

interface Props {
  variant?: ToastVariant
  title: string
  description?: string
  dismissible?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'info',
  description: undefined,
  dismissible: false,
})

defineEmits<{
  close: []
}>()

const variantIcons: Record<ToastVariant, Component> = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

const variantClasses: Record<ToastVariant, string> = {
  success: 'bg-success-50 border-success-100 text-success-700',
  error: 'bg-danger-50 border-danger-100 text-danger-700',
  warning: 'bg-warning-50 border-warning-100 text-warning-700',
  info: 'bg-info-50 border-info-100 text-info-700',
}

const icon = computed(() => variantIcons[props.variant])
</script>

<template>
  <div class="flex items-start gap-3 rounded-lg border p-4" :class="variantClasses[variant]" role="alert">
    <component :is="icon" class="mt-0.5 h-5 w-5 shrink-0" />
    <div class="flex-1">
      <p class="text-sm font-semibold">{{ title }}</p>
      <p v-if="description" class="mt-0.5 text-sm opacity-90">{{ description }}</p>
    </div>
    <button
      v-if="dismissible"
      type="button"
      aria-label="Dismiss alert"
      class="opacity-70 hover:opacity-100"
      @click="$emit('close')"
    >
      <X class="h-4 w-4" />
    </button>
  </div>
</template>
