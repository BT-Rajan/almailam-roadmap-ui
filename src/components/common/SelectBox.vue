<script setup lang="ts">
import { ChevronDown } from '@lucide/vue'
import { computed, useId } from 'vue'

import type { SelectOption } from '@/types/Ui'

interface Props {
  modelValue: string
  options: SelectOption[]
  label?: string
  placeholder?: string
  error?: string
  disabled?: boolean
  required?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  label: undefined,
  placeholder: 'Select an option',
  error: undefined,
  disabled: false,
  required: false,
})

defineEmits<{
  'update:modelValue': [value: string]
}>()

const selectId = useId()

const selectClasses = computed(() => [
  'h-10 w-full appearance-none rounded-lg border bg-bg-card px-3 pr-9 text-sm text-neutral-800',
  'transition-colors duration-fast',
  'focus:outline-none focus:ring-2 focus:ring-primary-500/30',
  props.error ? 'border-danger-500' : 'border-border-default focus:border-primary-500',
  props.disabled ? 'cursor-not-allowed bg-bg-secondary text-neutral-400' : '',
])
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="selectId" class="text-sm font-medium text-neutral-700">
      {{ label }}
      <span v-if="required" class="text-danger-500">*</span>
    </label>
    <div class="relative">
      <select
        :id="selectId"
        :value="modelValue"
        :disabled="disabled"
        :required="required"
        :class="selectClasses"
        :aria-invalid="Boolean(error)"
        @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
      >
        <option value="" disabled>{{ placeholder }}</option>
        <option v-for="option in options" :key="option.value" :value="option.value">
          {{ option.label }}
        </option>
      </select>
      <ChevronDown
        class="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400"
      />
    </div>
    <p v-if="error" class="text-xs text-danger-500">{{ error }}</p>
  </div>
</template>
