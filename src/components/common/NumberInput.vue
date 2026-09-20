<script setup lang="ts">
import { computed, useId } from 'vue'

interface Props {
  modelValue: number | string
  label?: string
  placeholder?: string
  hint?: string
  error?: string
  disabled?: boolean
  required?: boolean
  min?: number
  max?: number
  step?: number | string
  // Short unit shown inside the field ahead of the number (e.g. a
  // currency code) -- purely visual, never part of the value.
  prefix?: string
}

const props = withDefaults(defineProps<Props>(), {
  label: undefined,
  placeholder: undefined,
  hint: undefined,
  error: undefined,
  disabled: false,
  required: false,
  min: undefined,
  max: undefined,
  step: 1,
  prefix: undefined,
})

defineEmits<{
  'update:modelValue': [value: string]
}>()

const inputId = useId()

// Leaves room for the prefix inside the field: the start padding plus
// about 0.75em per (uppercase) character, in the input's own font size,
// so it tracks the prefix length instead of assuming a fixed width.
const prefixPadding = computed(() =>
  props.prefix ? { paddingInlineStart: `calc(1.125rem + ${(props.prefix.length * 0.75).toFixed(2)}em)` } : undefined,
)

const inputClasses = computed(() => [
  'h-10 w-full rounded-lg border bg-bg-card text-sm text-text-primary',
  'placeholder:text-text-muted',
  'transition-colors duration-fast',
  'focus:outline-none focus:ring-2 focus:ring-accent-500/30',
  'px-3',
  props.error ? 'border-danger-500' : 'border-border-default focus:border-accent-500',
  props.disabled ? 'cursor-not-allowed bg-bg-secondary text-text-muted' : '',
])
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="inputId" class="text-sm font-medium text-text-secondary">
      {{ label }}
      <span v-if="required" class="text-danger-500">*</span>
    </label>
    <div class="relative">
      <!-- z-10: every .bg-bg-* surface (this input included) gets a
           backdrop-filter from the glass theme in main.css, which makes it
           paint above earlier positioned siblings -- without a z-index the
           translucent input covered this prefix and left it barely visible. -->
      <span v-if="prefix" class="pointer-events-none absolute inset-y-0 start-3 z-10 flex items-center text-sm font-medium text-text-muted" aria-hidden="true">
        {{ prefix }}
      </span>
      <input
        :id="inputId"
        type="number"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :min="min"
        :max="max"
        :step="step"
        :class="inputClasses"
        :style="prefixPadding"
        :aria-invalid="Boolean(error)"
        :aria-describedby="error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      />
    </div>
    <p v-if="error" :id="`${inputId}-error`" class="text-xs text-danger-500">{{ error }}</p>
    <p v-else-if="hint" :id="`${inputId}-hint`" class="text-xs text-text-muted">{{ hint }}</p>
  </div>
</template>
