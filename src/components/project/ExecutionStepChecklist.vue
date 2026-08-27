<script setup lang="ts">
import { Plus, Trash2 } from '@lucide/vue'
import { computed, reactive, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import IconButton from '@/components/common/IconButton.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { EXECUTION_STEP_STAGE_OPTIONS } from '@/utils/projectHelpers'
import type { ExecutionStepBulkItem, ProjectExecutionStep } from '@/types/ExecutionStep'
import type { SelectOption } from '@/types/Ui'

const props = defineProps<{
  steps: ProjectExecutionStep[]
  isSaving: boolean
}>()

const emit = defineEmits<{
  save: [items: ExecutionStepBulkItem[]]
  'add-step': [name: string, weightPercentage: number, stageKey: string]
  'remove-step': [stepId: string]
}>()

const STAGE_OPTIONS: SelectOption[] = EXECUTION_STEP_STAGE_OPTIONS.map((stage) => ({ value: stage, label: stage }))

const newStepName = ref('')
const newStepWeight = ref(5)
const newStepStageKey = ref(STAGE_OPTIONS[0]?.value ?? '')

function submitNewStep(): void {
  if (newStepName.value.trim().length === 0 || newStepWeight.value <= 0 || !newStepStageKey.value) return
  emit('add-step', newStepName.value.trim(), newStepWeight.value, newStepStageKey.value)
  newStepName.value = ''
  newStepWeight.value = 5
}

interface Draft {
  done: boolean
  isExcluded: boolean
  excludedReason: string
  remarks: string
}

// One draft object per step, keyed by step id -- checking a box only
// stages a change locally; nothing reaches the server until Save is
// pressed once for the whole list (that's the point: 23 rows, 1
// network call, not 23).
const drafts = reactive<Record<string, Draft>>({})

function seedFrom(steps: ProjectExecutionStep[]): void {
  for (const step of steps) {
    drafts[step.id] = {
      done: step.completionPercentage >= 100,
      isExcluded: step.isExcluded,
      excludedReason: step.excludedReason ?? '',
      remarks: step.remarks ?? '',
    }
  }
}

seedFrom(props.steps)
// Re-seed whenever the server's copy changes (e.g. after Save resolves
// and the store swaps in the refreshed list) so the draft baseline for
// the dirty check below tracks what's actually saved.
watch(() => props.steps, seedFrom)

function isRowDirty(step: ProjectExecutionStep): boolean {
  const draft = drafts[step.id]
  if (!draft) return false
  return (
    draft.done !== step.completionPercentage >= 100 ||
    draft.isExcluded !== step.isExcluded ||
    draft.excludedReason !== (step.excludedReason ?? '') ||
    draft.remarks !== (step.remarks ?? '')
  )
}

const isDirty = computed(() => props.steps.some((step) => isRowDirty(step)))

const includedSteps = computed(() => props.steps.filter((s) => !drafts[s.id]?.isExcluded))
const doneCount = computed(() => includedSteps.value.filter((s) => drafts[s.id]?.done).length)

function handleSave(): void {
  const items: ExecutionStepBulkItem[] = props.steps
    .filter((step) => isRowDirty(step))
    .map((step) => {
      const draft = drafts[step.id]
      return {
        id: step.id,
        completionPercentage: draft.done ? 100 : 0,
        remarks: draft.remarks.trim() || null,
        isExcluded: draft.isExcluded,
        excludedReason: draft.isExcluded ? draft.excludedReason.trim() || null : null,
      }
    })
  if (items.length === 0) return
  emit('save', items)
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <div class="flex items-center justify-between gap-3">
      <p class="text-xs text-text-muted">{{ doneCount }} of {{ includedSteps.length }} included activities complete</p>
      <BaseButton size="sm" :disabled="!isDirty" :loading="isSaving" @click="handleSave">Save Checklist</BaseButton>
    </div>

    <ol class="flex flex-col divide-y divide-border-light">
      <li
        v-for="step in steps"
        :key="step.id"
        class="flex flex-col gap-2 py-2.5 first:pt-0 last:pb-0"
        :class="drafts[step.id]?.isExcluded ? 'opacity-50' : ''"
      >
        <div class="flex items-start gap-3">
          <div class="min-w-0 flex-1">
            <Checkbox
              v-if="drafts[step.id]"
              v-model="drafts[step.id].done"
              :disabled="isSaving || drafts[step.id].isExcluded"
              :label="step.isOptional ? `${step.name} (optional)` : step.name"
              :hint="`${step.weightPercentage}% weight`"
            />
          </div>
          <label v-if="drafts[step.id]" class="flex shrink-0 items-center gap-1.5 text-xs text-text-muted">
            <input
              type="checkbox"
              class="h-3.5 w-3.5 rounded border-border-default"
              :checked="drafts[step.id].isExcluded"
              :disabled="isSaving"
              @change="drafts[step.id].isExcluded = ($event.target as HTMLInputElement).checked"
            />
            Not applicable to this project
          </label>
          <IconButton
            v-if="step.isCustom"
            :icon="Trash2"
            label="Remove step"
            size="sm"
            variant="danger"
            :disabled="isSaving"
            @click="emit('remove-step', step.id)"
          />
        </div>

        <TextInput
          v-if="drafts[step.id]?.isExcluded"
          v-model="drafts[step.id].excludedReason"
          placeholder="Why doesn't this apply? (optional)"
          :disabled="isSaving"
        />
        <TextInput
          v-else-if="drafts[step.id]"
          v-model="drafts[step.id].remarks"
          placeholder="Remarks (optional)"
          :disabled="isSaving"
        />
      </li>
    </ol>

    <div class="flex flex-col gap-3 rounded-lg border border-dashed border-border-default p-4">
      <p class="text-sm font-medium text-text-secondary">Add Activity</p>
      <p class="text-xs text-text-muted">
        Beyond this project's assigned checklist -- e.g. extra work this specific project turned out to need.
      </p>
      <div class="flex flex-col gap-2 sm:flex-row sm:items-center">
        <TextInput v-model="newStepName" placeholder="Activity name" class="sm:flex-1" :disabled="isSaving" />
        <div class="flex items-center gap-1">
          <input
            v-model.number="newStepWeight"
            type="number"
            min="0.01"
            max="100"
            step="0.01"
            :disabled="isSaving"
            class="w-20 rounded-lg border border-border-default bg-bg-card px-2 py-1.5 text-right text-sm text-text-primary"
          />
          <span class="text-xs text-text-muted">%</span>
        </div>
        <SelectBox v-model="newStepStageKey" :options="STAGE_OPTIONS" class="max-w-xs sm:flex-1" :disabled="isSaving" />
        <BaseButton :icon="Plus" variant="secondary" :disabled="isSaving || newStepName.trim().length === 0" @click="submitNewStep">
          Add
        </BaseButton>
      </div>
    </div>
  </div>
</template>
