<script setup lang="ts">
import { computed, useId } from 'vue'

interface Props {
  modelValue: string
  label?: string
  placeholder?: string
  hint?: string
  error?: string
  disabled?: boolean
  required?: boolean
  rows?: number
  maxLength?: number
}

const props = withDefaults(defineProps<Props>(), {
  label: undefined,
  placeholder: undefined,
  hint: undefined,
  error: undefined,
  disabled: false,
  required: false,
  rows: 4,
  maxLength: undefined,
})

defineEmits<{
  'update:modelValue': [value: string]
}>()

const textareaId = useId()

const textareaClasses = computed(() => [
  'w-full rounded-lg border bg-bg-card text-sm text-neutral-800 p-3',
  'placeholder:text-neutral-400',
  'transition-colors duration-fast',
  'focus:outline-none focus:ring-2 focus:ring-primary-500/30',
  'resize-vertical',
  props.error ? 'border-danger-500' : 'border-border-default focus:border-primary-500',
  props.disabled ? 'cursor-not-allowed bg-bg-secondary text-neutral-400' : '',
])

const charCount = computed(() => `${props.modelValue.length}${props.maxLength ? `/${props.maxLength}` : ''}`)
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="textareaId" class="text-sm font-medium text-neutral-700">
      {{ label }}
      <span v-if="required" class="text-danger-500">*</span>
    </label>
    <textarea
      :id="textareaId"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :rows="rows"
      :maxlength="maxLength"
      :class="textareaClasses"
      :aria-invalid="Boolean(error)"
      :aria-describedby="error ? `${textareaId}-error` : hint ? `${textareaId}-hint` : undefined"
      @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    />
    <div class="flex items-center justify-between gap-2">
      <div>
        <p v-if="error" :id="`${textareaId}-error`" class="text-xs text-danger-500">{{ error }}</p>
        <p v-else-if="hint" :id="`${textareaId}-hint`" class="text-xs text-neutral-400">{{ hint }}</p>
      </div>
      <p v-if="maxLength" class="text-xs text-neutral-400">{{ charCount }}</p>
    </div>
  </div>
</template>
