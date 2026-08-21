<script setup lang="ts">
import { reactive, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { PROCESS_STAGES } from '@/constants/processStages'
import type { ProjectDocument } from '@/types/Document'
import type { SelectOption } from '@/types/Ui'

const props = defineProps<{
  modelValue: boolean
  document: ProjectDocument | null
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: { title: string; stageKey: string | null }]
}>()

const STAGE_OPTIONS: SelectOption[] = PROCESS_STAGES.map((s) => ({ value: s.key, label: s.label }))

const form = reactive({ title: '', stageKey: '' })
const errors = reactive({ title: '' })

watch(
  () => props.modelValue,
  (open) => {
    if (!open || !props.document) return
    form.title = props.document.title
    form.stageKey = props.document.stageKey ?? ''
    errors.title = ''
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  errors.title = form.title.trim() ? '' : 'Title is required'
  if (errors.title) return

  emit('confirm', { title: form.title.trim(), stageKey: form.stageKey || null })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="Edit Document" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <TextInput v-model="form.title" label="Document Title" required :error="errors.title" />
      <SelectBox
        v-model="form.stageKey"
        label="Approval Process Stage (optional)"
        placeholder="Not tied to a specific stage"
        :options="STAGE_OPTIONS"
      />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">Save Changes</BaseButton>
    </template>
  </BaseDialog>
</template>
