<script setup lang="ts">
import { Check } from '@lucide/vue'
import { computed, useId } from 'vue'
import { useI18n } from 'vue-i18n'
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
const { t } = useI18n()

function optionLabel(option: SelectOption): string {
  return option.labelKey ? t(option.labelKey) : option.label
}

const containerClasses = computed(() => [
  'flex gap-4',
  props.vertical ? 'flex-col' : 'flex-row flex-wrap',
])
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <div v-if="label">
      <p class="text-sm font-medium text-text-secondary">
        {{ label }}
      </p>
      <p v-if="hint" class="text-xs text-text-muted mt-0.5">{{ hint }}</p>
    </div>
    <div :class="containerClasses">
      <label
        v-for="option in options"
        :key="option.value"
        :for="`${groupId}-${option.value}`"
        class="flex items-center gap-2"
        :class="disabled ? 'cursor-not-allowed' : 'cursor-pointer'"
      >
        <div class="relative flex h-5 w-5 items-center justify-center rounded-full border-2 border-border-default bg-bg-card transition-colors duration-fast has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-accent-500/30 has-[:focus-visible]:ring-offset-2">
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
            class="absolute inset-0 rounded-full hover:bg-bg-hover transition-colors duration-fast pointer-events-none"
          />
          <div v-if="modelValue === option.value" class="absolute inset-0 rounded-full border-2 border-primary-500/30 pointer-events-none" />
        </div>
        <span class="text-sm text-text-secondary" :class="disabled ? 'text-text-muted' : ''">
          {{ optionLabel(option) }}
        </span>
      </label>
    </div>
  </div>
</template>
