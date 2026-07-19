<script setup lang="ts">
import { Calendar } from '@lucide/vue'
import { computed, useId } from 'vue'

interface Props {
  modelValue: string
  label?: string
  placeholder?: string
  hint?: string
  error?: string
  disabled?: boolean
  required?: boolean
  min?: string
  max?: string
}

const props = withDefaults(defineProps<Props>(), {
  label: undefined,
  placeholder: 'Select a date',
  hint: undefined,
  error: undefined,
  disabled: false,
  required: false,
  min: undefined,
  max: undefined,
})

defineEmits<{
  'update:modelValue': [value: string]
}>()

const inputId = useId()

const inputClasses = computed(() => [
  'h-10 w-full rounded-lg border bg-bg-card text-sm text-neutral-800',
  'placeholder:text-neutral-400',
  'transition-colors duration-fast',
  'focus:outline-none focus:ring-2 focus:ring-primary-500/30',
  'pl-10 pr-3',
  props.error ? 'border-danger-500' : 'border-border-default focus:border-primary-500',
  props.disabled ? 'cursor-not-allowed bg-bg-secondary text-neutral-400' : '',
])
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="inputId" class="text-sm font-medium text-neutral-700">
      {{ label }}
      <span v-if="required" class="text-danger-500">*</span>
    </label>
    <div class="relative">
      <Calendar
        class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400"
      />
      <input
        :id="inputId"
        type="date"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :min="min"
        :max="max"
        :class="inputClasses"
        :aria-invalid="Boolean(error)"
        :aria-describedby="error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      />
    </div>
    <p v-if="error" :id="`${inputId}-error`" class="text-xs text-danger-500">{{ error }}</p>
    <p v-else-if="hint" :id="`${inputId}-hint`" class="text-xs text-neutral-400">{{ hint }}</p>
  </div>
</template>
