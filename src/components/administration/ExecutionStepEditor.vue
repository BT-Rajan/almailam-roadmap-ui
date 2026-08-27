<script setup lang="ts">
import { ArrowDown, ArrowUp, Plus, Trash2 } from '@lucide/vue'
import { ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import IconButton from '@/components/common/IconButton.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { EXECUTION_STEP_STAGE_OPTIONS } from '@/utils/projectHelpers'
import type { ExecutionStepTemplateItem } from '@/types/ExecutionStep'
import type { SelectOption } from '@/types/Ui'

defineProps<{
  steps: ExecutionStepTemplateItem[]
}>()

const emit = defineEmits<{
  update: [
    stepId: string,
    fields: { name?: string; weightPercentage?: number; stageKey?: string; isOptional?: boolean; triggerKey?: string },
  ]
  remove: [stepId: string]
  move: [stepId: string, direction: 'up' | 'down']
  add: [name: string, weightPercentage: number, stageKey: string, isOptional: boolean, triggerKey: string]
}>()

// Which of the 7 project workflow stages this activity is expected to
// happen during -- e.g. "Client Civil ID collected" during Contract,
// "Architectural drawings completed" during Design. Not to be confused
// with the 5 Project Approval Process gates (Documents Signed, MEW
// Approval, etc.) -- those are separate, external sign-offs tracked on
// their own tab, not something an execution activity is filed under.
const STAGE_OPTIONS: SelectOption[] = EXECUTION_STEP_STAGE_OPTIONS.map((stage) => ({
  value: stage,
  label: stage,
}))

// The fixed set of real-world events a step can be wired to -- '' means
// none, which is the overwhelming majority (actual design/drawing
// production work with nothing else in the app tracking it). Mirrors
// execution_step_service.TRIGGER_KEYS exactly; a typo'd value would
// silently never fire, so this is a picklist, not free text.
const TRIGGER_KEY_OPTIONS: SelectOption[] = [
  { value: '', label: 'None -- manual only' },
  { value: 'quotation_created', label: 'Quotation created' },
  { value: 'contract_created', label: 'Contract created' },
  { value: 'gate:documents_signed', label: 'Gate: Documents signed' },
  { value: 'gate:mew_approval', label: 'Gate: MEW approval' },
  { value: 'gate:architectural_approval', label: 'Gate: Architectural approval' },
  { value: 'gate:submit_baladia_kfd', label: 'Gate: Baladia/KFD submission' },
]

const newStepName = ref('')
const newStepWeight = ref(5)
const newStepStageKey = ref(STAGE_OPTIONS[0]?.value ?? '')
const newStepIsOptional = ref(false)
const newStepTriggerKey = ref('')

function submitNewStep(): void {
  if (newStepName.value.trim().length === 0 || newStepWeight.value <= 0 || !newStepStageKey.value) return
  emit('add', newStepName.value.trim(), newStepWeight.value, newStepStageKey.value, newStepIsOptional.value, newStepTriggerKey.value)
  newStepName.value = ''
  newStepWeight.value = 5
  newStepIsOptional.value = false
  newStepTriggerKey.value = ''
}

// Local drafts of in-progress edits, keyed by step id, so typing doesn't
// fire a save on every keystroke -- only once the field loses focus,
// and only if the value actually changed.
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

function commitStage(step: ExecutionStepTemplateItem, value: string): void {
  if (value !== step.stageKey) emit('update', step.id, { stageKey: value })
}

function commitOptional(step: ExecutionStepTemplateItem, value: boolean): void {
  if (value !== step.isOptional) emit('update', step.id, { isOptional: value })
}

function commitTrigger(step: ExecutionStepTemplateItem, value: string): void {
  if (value !== (step.triggerKey ?? '')) emit('update', step.id, { triggerKey: value })
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <ol class="flex flex-col gap-3">
      <li
        v-for="(step, index) in steps"
        :key="step.id"
        class="flex flex-col gap-3 rounded-lg border border-border-light bg-bg-card p-4"
      >
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
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
        </div>

        <div class="flex flex-wrap items-center gap-4 pl-9">
          <SelectBox
            :model-value="step.stageKey"
            :options="STAGE_OPTIONS"
            class="max-w-xs flex-1"
            @update:model-value="commitStage(step, $event)"
          />
          <SelectBox
            :model-value="step.triggerKey ?? ''"
            :options="TRIGGER_KEY_OPTIONS"
            class="max-w-xs flex-1"
            @update:model-value="commitTrigger(step, $event)"
          />
          <Checkbox
            :model-value="step.isOptional"
            label="Waivable"
            hint="Clients can waive this step instead of completing it"
            @update:model-value="commitOptional(step, Boolean($event))"
          />
        </div>
      </li>
    </ol>

    <div class="flex flex-col gap-3 rounded-lg border border-dashed border-border-default p-4">
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
      <div class="flex flex-wrap items-center gap-4">
        <SelectBox v-model="newStepStageKey" :options="STAGE_OPTIONS" class="max-w-xs flex-1" />
        <SelectBox v-model="newStepTriggerKey" :options="TRIGGER_KEY_OPTIONS" class="max-w-xs flex-1" />
        <Checkbox v-model="newStepIsOptional" label="Waivable" />
      </div>
    </div>
  </div>
</template>
