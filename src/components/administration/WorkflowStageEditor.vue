<script setup lang="ts">
import { ArrowDown, ArrowUp, Plus, Trash2 } from '@lucide/vue'
import { ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import IconButton from '@/components/common/IconButton.vue'
import TextInput from '@/components/common/TextInput.vue'
import type { WorkflowStageConfig } from '@/types/Workflow'

defineProps<{
  stages: WorkflowStageConfig[]
}>()

const emit = defineEmits<{
  update: [stageId: string, fields: Partial<Pick<WorkflowStageConfig, 'name' | 'description'>>]
  remove: [stageId: string]
  move: [stageId: string, direction: 'up' | 'down']
  add: [name: string, description: string]
}>()

const newStageName = ref('')
const newStageDescription = ref('')

function submitNewStage(): void {
  if (newStageName.value.trim().length === 0) return
  emit('add', newStageName.value.trim(), newStageDescription.value.trim())
  newStageName.value = ''
  newStageDescription.value = ''
}
</script>

<template>
  <div class="flex flex-col gap-4">
    <ol class="flex flex-col gap-3">
      <li
        v-for="(stage, index) in stages"
        :key="stage.id"
        class="flex flex-col gap-3 rounded-lg border border-border-light bg-bg-card p-4 sm:flex-row sm:items-start"
      >
        <span class="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary-50 text-xs font-semibold text-primary-600">
          {{ index + 1 }}
        </span>

        <div class="flex flex-1 flex-col gap-2">
          <TextInput
            :model-value="stage.name"
            placeholder="Stage name"
            @update:model-value="emit('update', stage.id, { name: $event })"
          />
          <TextInput
            :model-value="stage.description"
            placeholder="Stage description"
            @update:model-value="emit('update', stage.id, { description: $event })"
          />
        </div>

        <div class="flex shrink-0 items-center gap-1 self-end sm:self-start">
          <IconButton :icon="ArrowUp" label="Move up" size="sm" :disabled="index === 0" @click="emit('move', stage.id, 'up')" />
          <IconButton
            :icon="ArrowDown"
            label="Move down"
            size="sm"
            :disabled="index === stages.length - 1"
            @click="emit('move', stage.id, 'down')"
          />
          <IconButton :icon="Trash2" label="Remove stage" size="sm" variant="danger" @click="emit('remove', stage.id)" />
        </div>
      </li>
    </ol>

    <div class="flex flex-col gap-2 rounded-lg border border-dashed border-border-default p-4">
      <p class="text-sm font-medium text-neutral-700">Add Stage</p>
      <div class="flex flex-col gap-2 sm:flex-row">
        <TextInput v-model="newStageName" placeholder="Stage name" class="sm:flex-1" />
        <TextInput v-model="newStageDescription" placeholder="Stage description" class="sm:flex-1" />
        <BaseButton :icon="Plus" variant="secondary" :disabled="newStageName.trim().length === 0" @click="submitNewStage">
          Add
        </BaseButton>
      </div>
    </div>
  </div>
</template>
