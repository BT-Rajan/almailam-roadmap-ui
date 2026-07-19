<script setup lang="ts">
import { Check } from '@lucide/vue'
import { computed } from 'vue'

interface WizardStep {
  label: string
  description?: string
}

interface Props {
  steps: WizardStep[]
  currentStep: number
}

const props = defineProps<Props>()

function stepStatus(index: number): 'complete' | 'current' | 'upcoming' {
  if (index < props.currentStep) return 'complete'
  if (index === props.currentStep) return 'current'
  return 'upcoming'
}

const circleClasses = computed(() => (index: number) => {
  const status = stepStatus(index)
  return [
    'flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 text-sm font-semibold transition-colors duration-fast',
    status === 'complete' ? 'border-primary-500 bg-primary-500 text-white' : '',
    status === 'current' ? 'border-primary-500 bg-bg-card text-primary-600' : '',
    status === 'upcoming' ? 'border-border-default bg-bg-card text-neutral-400' : '',
  ]
})

function connectorClasses(index: number): string[] {
  return [
    'h-0.5 flex-1 transition-colors duration-fast',
    index < props.currentStep ? 'bg-primary-500' : 'bg-border-default',
  ]
}
</script>

<template>
  <ol class="flex items-start">
    <li v-for="(step, index) in steps" :key="step.label" class="flex flex-1 items-center last:flex-none">
      <div class="flex flex-col items-center gap-2 text-center">
        <div :class="circleClasses(index)">
          <Check v-if="stepStatus(index) === 'complete'" class="h-4 w-4" />
          <span v-else>{{ index + 1 }}</span>
        </div>
        <div class="max-w-[7rem]">
          <p
            class="text-xs font-medium"
            :class="stepStatus(index) === 'upcoming' ? 'text-neutral-400' : 'text-neutral-700'"
          >
            {{ step.label }}
          </p>
          <p v-if="step.description" class="text-[11px] text-neutral-400">{{ step.description }}</p>
        </div>
      </div>
      <div v-if="index < steps.length - 1" :class="connectorClasses(index)" class="mx-3 mt-4" />
    </li>
  </ol>
</template>
