<script setup lang="ts">
import { ArrowDown, ArrowUp, Plus, Trash2 } from '@lucide/vue'
import { ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import IconButton from '@/components/common/IconButton.vue'
import TextInput from '@/components/common/TextInput.vue'
import type { ExecutionStepTemplateItem } from '@/types/ExecutionStep'

defineProps<{
  steps: ExecutionStepTemplateItem[]
}>()

const emit = defineEmits<{
  update: [stepId: string, fields: { name?: string; weightPercentage?: number }]
  remove: [stepId: string]
  move: [stepId: string, direction: 'up' | 'down']
  add: [name: string, weightPercentage: number]
}>()

const newStepName = ref('')
const newStepWeight = ref(5)

function submitNewStep(): void {
  if (newStepName.value.trim().length === 0 || newStepWeight.value <= 0) return
  emit('add', newStepName.value.trim(), newStepWeight.value)
  newStepName.value = ''
  newStepWeight.value = 5
}

// Local drafts of in-progress edits, keyed by step id, so typing doesn't
// fire a save on every keystroke -- only once the field loses focus,
// and only if the value actually changed. Same pattern as
// WorkflowStageEditor.vue.
const nameDrafts = ref<Record<string, string>>({})
const weightDrafts = ref<Record<string, number>>({})

function commitName(step: ExecutionStepTemplateItem, value: string): void {
  delete nameDrafts.value[step.id]
  if (value !== step.name) emit('update', step.id, { name: value })
}

function commitWeight(step: ExecutionStepTemplateItem, value: number): void {
  delete weightDrafts.value[step.id]
  if (value !== step.weightPercentage && value > 0) emit('update', step.id, { weightPercentage: value })
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <ol class="flex flex-col gap-3">
      <li
        v-for="(step, index) in steps"
        :key="step.id"
        class="flex flex-col gap-3 rounded-lg border border-border-light bg-bg-card p-4 sm:flex-row sm:items-center"
      >
        <span class="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary-50 text-xs font-semibold text-primary-600">
          {{ index + 1 }}
        </span>

        <TextInput
          :model-value="nameDrafts[step.id] ?? step.name"
          placeholder="Step name"
          class="flex-1"
          @update:model-value="nameDrafts[step.id] = $event"
          @blur="commitName(step, $event)"
        />

        <div class="flex items-center gap-1">
          <input
            :value="weightDrafts[step.id] ?? step.weightPercentage"
            type="number"
            min="0.01"
            max="100"
            step="0.01"
            class="w-20 rounded-lg border border-border-default bg-bg-card px-2 py-1.5 text-right text-sm text-text-primary"
            @input="weightDrafts[step.id] = Number(($event.target as HTMLInputElement).value)"
            @blur="commitWeight(step, weightDrafts[step.id] ?? step.weightPercentage)"
          />
          <span class="text-xs text-text-muted">%</span>
        </div>

        <div class="flex shrink-0 items-center gap-1 self-end sm:self-auto">
          <IconButton :icon="ArrowUp" label="Move up" size="sm" :disabled="index === 0" @click="emit('move', step.id, 'up')" />
          <IconButton
            :icon="ArrowDown"
            label="Move down"
            size="sm"
            :disabled="index === steps.length - 1"
            @click="emit('move', step.id, 'down')"
          />
          <IconButton :icon="Trash2" label="Remove step" size="sm" variant="danger" @click="emit('remove', step.id)" />
        </div>
      </li>
    </ol>

    <div class="flex flex-col gap-2 rounded-lg border border-dashed border-border-default p-4">
      <p class="text-sm font-medium text-text-secondary">Add Step</p>
      <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
        <TextInput v-model="newStepName" placeholder="Step name" class="sm:flex-1" />
        <div class="flex items-center gap-1">
          <input
            v-model.number="newStepWeight"
            type="number"
            min="0.01"
            max="100"
            step="0.01"
            class="w-20 rounded-lg border border-border-default bg-bg-card px-2 py-1.5 text-right text-sm text-text-primary"
          />
          <span class="text-xs text-text-muted">%</span>
        </div>
        <BaseButton :icon="Plus" variant="secondary" :disabled="newStepName.trim().length === 0" @click="submitNewStep">
          Add
        </BaseButton>
      </div>
    </div>
  </div>
</template>
