<script setup lang="ts">
import { Check } from '@lucide/vue'
import { computed, useId } from 'vue'
import type { SelectOption } from '@/types/Ui'

interface Props {
  modelValue: string | number
  options: SelectOption[]
  label?: string
  hint?: string
  disabled?: boolean
  vertical?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  label: undefined,
  hint: undefined,
  disabled: false,
  vertical: true,
})

defineEmits<{
  'update:modelValue': [value: string | number]
}>()

const groupId = useId()

const containerClasses = computed(() => [
  'flex gap-4',
  props.vertical ? 'flex-col' : 'flex-row flex-wrap',
])
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <div v-if="label">
      <p class="text-sm font-medium text-neutral-700">
        {{ label }}
      </p>
      <p v-if="hint" class="text-xs text-neutral-400 mt-0.5">{{ hint }}</p>
    </div>
    <div :class="containerClasses">
      <div v-for="option in options" :key="option.value" class="flex items-center gap-2">
        <div class="relative flex h-5 w-5 items-center justify-center rounded-full border-2 border-border-default bg-bg-card transition-colors duration-fast">
          <input
            :id="`${groupId}-${option.value}`"
            type="radio"
            :name="groupId"
            :value="option.value"
            :checked="modelValue === option.value"
            :disabled="disabled"
            class="sr-only"
            @change="$emit('update:modelValue', option.value)"
          />
          <Check
            v-if="modelValue === option.value"
            class="h-3 w-3 text-primary-500 pointer-events-none"
          />
          <div
            v-if="!disabled"
            class="absolute inset-0 rounded-full hover:bg-bg-hover transition-colors duration-fast"
          />
          <div v-if="modelValue === option.value" class="absolute inset-0 rounded-full border-2 border-primary-500/30 pointer-events-none" />
        </div>
        <label :for="`${groupId}-${option.value}`" class="text-sm text-neutral-700 cursor-pointer" :class="disabled ? 'text-neutral-400' : ''">
          {{ option.label }}
        </label>
      </div>
    </div>
  </div>
</template>
