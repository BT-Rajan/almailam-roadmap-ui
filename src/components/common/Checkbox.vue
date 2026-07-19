<script setup lang="ts">
import { Check, Minus } from '@lucide/vue'
import { computed, useId } from 'vue'

interface Props {
  modelValue: boolean | string | number
  value?: string | number
  label?: string
  hint?: string
  disabled?: boolean
  indeterminate?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  value: undefined,
  label: undefined,
  hint: undefined,
  disabled: false,
  indeterminate: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean | string | number]
}>()

const checkboxId = useId()

const isChecked = computed(() => {
  if (props.value !== undefined) {
    if (Array.isArray(props.modelValue)) {
      return props.modelValue.includes(props.value)
    }
    return props.modelValue === props.value
  }
  return Boolean(props.modelValue)
})

const handleChange = (event: Event) => {
  const checkbox = event.target as HTMLInputElement
  if (props.value !== undefined) {
    if (Array.isArray(props.modelValue)) {
      const newValue = [...props.modelValue]
      if (checkbox.checked) {
        newValue.push(props.value)
      } else {
        newValue.splice(newValue.indexOf(props.value), 1)
      }
      emit('update:modelValue', newValue as unknown as string | number)
    } else {
      emit('update:modelValue', checkbox.checked ? props.value : false)
    }
  } else {
    emit('update:modelValue', checkbox.checked)
  }
}
</script>

<template>
  <div class="flex items-start gap-2.5">
    <div class="relative flex h-5 w-5 items-center justify-center rounded border border-border-default bg-bg-card transition-colors duration-fast">
      <input
        :id="checkboxId"
        type="checkbox"
        :checked="isChecked"
        :disabled="disabled"
        :aria-checked="indeterminate ? 'mixed' : isChecked"
        class="sr-only"
        @change="handleChange"
      />
      <Check
        v-if="isChecked && !indeterminate"
        class="h-3.5 w-3.5 text-primary-500 pointer-events-none"
      />
      <Minus
        v-else-if="indeterminate"
        class="h-3.5 w-3.5 text-primary-500 pointer-events-none"
      />
      <div
        v-if="!disabled"
        class="absolute inset-0 rounded border-border-default hover:bg-bg-hover transition-colors duration-fast"
      />
      <div v-if="isChecked || indeterminate" class="absolute inset-0 rounded border-2 border-primary-500/30 pointer-events-none" />
    </div>
    <div v-if="label || hint" class="flex flex-col gap-0.5">
      <label :for="checkboxId" class="text-sm font-medium text-neutral-700 cursor-pointer" :class="disabled ? 'text-neutral-400' : ''">
        {{ label }}
      </label>
      <p v-if="hint" class="text-xs text-neutral-400">{{ hint }}</p>
    </div>
  </div>
</template>
