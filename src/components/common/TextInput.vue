<script setup lang="ts">
import { computed, ref, useId } from 'vue'
import type { Component } from 'vue'

interface Props {
  modelValue: string | number
  label?: string
  placeholder?: string
  type?: 'text' | 'email' | 'password' | 'number' | 'tel'
  inputmode?: 'text' | 'numeric' | 'tel' | 'email' | 'url' | 'search' | 'decimal' | 'none'
  autocomplete?: string
  icon?: Component
  hint?: string
  error?: string
  disabled?: boolean
  required?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  label: undefined,
  placeholder: undefined,
  type: 'text',
  inputmode: undefined,
  autocomplete: undefined,
  icon: undefined,
  hint: undefined,
  error: undefined,
  disabled: false,
  required: false,
})

defineEmits<{
  'update:modelValue': [value: string]
  blur: [value: string]
}>()

const inputId = useId()
const inputRef = ref<HTMLInputElement>()

defineExpose({
  focus: (options?: FocusOptions) => inputRef.value?.focus(options),
})

const inputClasses = computed(() => [
  'h-10 w-full rounded-lg border bg-bg-card text-sm text-text-primary',
  'placeholder:text-text-muted',
  'transition-colors duration-fast',
  'focus:outline-none focus:ring-2 focus:ring-accent-500/30',
  props.icon ? 'ps-10 pe-3' : 'px-3',
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
      <component
        :is="icon"
        v-if="icon"
        class="pointer-events-none absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted"
      />
      <input
        :id="inputId"
        ref="inputRef"
        :type="type"
        :inputmode="inputmode"
        :autocomplete="autocomplete"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        :required="required"
        :class="inputClasses"
        :aria-invalid="Boolean(error)"
        :aria-describedby="error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        @blur="$emit('blur', ($event.target as HTMLInputElement).value)"
      />
    </div>
    <p v-if="error" :id="`${inputId}-error`" class="text-xs text-danger-500">{{ error }}</p>
    <p v-else-if="hint" :id="`${inputId}-hint`" class="text-xs text-text-muted">{{ hint }}</p>
  </div>
</template>
