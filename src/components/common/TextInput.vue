<script setup lang="ts">
import { Eye, EyeOff } from '@lucide/vue'
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
  // Only meaningful when type="password" -- adds an eye/eye-off button
  // that toggles the field between masked and plain text, since a
  // password field with no way to check what was actually typed makes
  // paste/typo mistakes (stray trailing space, wrong case) invisible
  // until a save or test fails against it.
  showPasswordToggle?: boolean
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
  showPasswordToggle: false,
})

defineEmits<{
  'update:modelValue': [value: string]
  blur: [value: string]
}>()

const inputId = useId()
const inputRef = ref<HTMLInputElement>()
const isRevealed = ref(false)

defineExpose({
  focus: (options?: FocusOptions) => inputRef.value?.focus(options),
})

const isPasswordToggle = computed(() => props.type === 'password' && props.showPasswordToggle)
const resolvedType = computed(() => (isPasswordToggle.value && isRevealed.value ? 'text' : props.type))

const inputClasses = computed(() => [
  'h-10 w-full rounded-lg border bg-bg-card text-sm text-text-primary',
  'placeholder:text-text-muted',
  'transition-colors duration-fast',
  'focus:outline-none focus:ring-2 focus:ring-accent-500/30',
  props.icon ? 'ps-10 pe-3' : 'px-3',
  isPasswordToggle.value ? 'pe-10' : '',
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
        :type="resolvedType"
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
      <button
        v-if="isPasswordToggle"
        type="button"
        tabindex="-1"
        class="absolute end-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
        :aria-label="isRevealed ? 'Hide password' : 'Show password'"
        @click="isRevealed = !isRevealed"
      >
        <component :is="isRevealed ? EyeOff : Eye" class="h-4 w-4" />
      </button>
    </div>
    <p v-if="error" :id="`${inputId}-error`" class="text-xs text-danger-500">{{ error }}</p>
    <p v-else-if="hint" :id="`${inputId}-hint`" class="text-xs text-text-muted">{{ hint }}</p>
  </div>
</template>

