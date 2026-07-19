<script setup lang="ts">
import { AlertTriangle, CheckCircle2, Info, X, XCircle } from '@lucide/vue'
import { computed } from 'vue'
import type { Component } from 'vue'

import type { ToastMessage, ToastVariant } from '@/types/Toast'

interface Props {
  toast: ToastMessage
}

const props = defineProps<Props>()

defineEmits<{
  dismiss: [id: string]
}>()

const variantIcons: Record<ToastVariant, Component> = {
  success: CheckCircle2,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

const variantClasses: Record<ToastVariant, string> = {
  success: 'text-success-500',
  error: 'text-danger-500',
  warning: 'text-warning-500',
  info: 'text-info-500',
}

const icon = computed(() => variantIcons[props.toast.variant])
</script>

<template>
  <div
    class="flex w-80 items-start gap-3 rounded-lg border border-border-light bg-bg-card p-4 shadow-elevated"
    role="alert"
  >
    <component :is="icon" class="mt-0.5 h-5 w-5 shrink-0" :class="variantClasses[toast.variant]" />
    <div class="flex-1">
      <p class="text-sm font-semibold text-neutral-800">{{ toast.title }}</p>
      <p v-if="toast.description" class="mt-0.5 text-sm text-neutral-500">{{ toast.description }}</p>
    </div>
    <button
      type="button"
      aria-label="Dismiss notification"
      class="text-neutral-400 hover:text-neutral-600"
      @click="$emit('dismiss', toast.id)"
    >
      <X class="h-4 w-4" />
    </button>
  </div>
</template>
