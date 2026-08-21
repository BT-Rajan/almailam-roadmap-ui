<script setup lang="ts">
import NumberInput from '@/components/common/NumberInput.vue'

interface Props {
  modelValue: number
  disabled?: boolean
}

withDefaults(defineProps<Props>(), { disabled: false })

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

const QUICK_MARKS = [20, 40, 60, 80, 100]

function clampPercentage(raw: number): number {
  if (Number.isNaN(raw)) return 0
  return Math.max(0, Math.min(100, Math.round(raw)))
}

function handleSlide(event: Event): void {
  emit('update:modelValue', clampPercentage(Number((event.target as HTMLInputElement).value)))
}

function handleNumberInput(value: string): void {
  emit('update:modelValue', clampPercentage(Number(value)))
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <div class="flex items-center gap-3">
      <input
        type="range"
        min="0"
        max="100"
        step="1"
        :value="modelValue"
        :disabled="disabled"
        class="h-2 w-full min-w-[160px] flex-1 cursor-pointer appearance-none rounded-full bg-bg-secondary accent-primary-600 disabled:cursor-not-allowed"
        :aria-label="`Completion percentage: ${modelValue}%`"
        @input="handleSlide"
      />
      <div class="w-20 shrink-0">
        <NumberInput
          :model-value="modelValue"
          :min="0"
          :max="100"
          :disabled="disabled"
          @update:model-value="handleNumberInput"
        />
      </div>
      <span class="w-4 shrink-0 text-xs text-text-muted">%</span>
    </div>
    <div class="flex items-center gap-1.5 no-print">
      <button
        v-for="mark in QUICK_MARKS"
        :key="mark"
        type="button"
        :disabled="disabled"
        class="rounded-md border px-2 py-0.5 text-xs font-medium transition-colors duration-fast disabled:cursor-not-allowed disabled:opacity-50"
        :class="
          modelValue === mark
            ? 'border-primary-600 bg-primary-600 text-white'
            : 'border-border-default text-text-secondary hover:bg-bg-hover'
        "
        @click="emit('update:modelValue', mark)"
      >
        {{ mark }}%
      </button>
    </div>
  </div>
</template>
