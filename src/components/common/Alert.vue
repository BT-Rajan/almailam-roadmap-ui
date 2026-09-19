<script setup lang="ts">
import { AlertTriangle, CheckCircle2, Info, X, XCircle } from '@lucide/vue'
import { computed } from 'vue'
import type { Component } from 'vue'
import { useI18n } from 'vue-i18n'

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
  success: 'border-success-100 border-l-success-500 bg-success-50 text-success-700',
  error: 'border-danger-100 border-l-danger-500 bg-danger-50 text-danger-700',
  warning: 'border-warning-100 border-l-warning-500 bg-warning-50 text-warning-700',
  info: 'border-info-100 border-l-info-500 bg-info-50 text-info-700',
}

const icon = computed(() => variantIcons[props.variant])
const { t } = useI18n()
</script>

<template>
  <div class="flex items-start gap-3 rounded-lg border border-l-4 p-4 shadow-glass-sm" :class="variantClasses[variant]" role="alert">
    <component :is="icon" class="mt-0.5 h-5 w-5 shrink-0" />
    <div class="flex-1">
      <p class="text-sm font-semibold">{{ title }}</p>
      <p v-if="description" class="mt-0.5 text-sm opacity-90">{{ description }}</p>
    </div>
    <div v-if="$slots.action" class="shrink-0">
      <slot name="action" />
    </div>
    <button
      v-if="dismissible"
      type="button"
      :aria-label="t('common.dismissAlert')"
      class="opacity-70 hover:opacity-100"
      @click="$emit('close')"
    >
      <X class="h-4 w-4" />
    </button>
  </div>
</template>
