<script setup lang="ts">
import { reactive, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import TextInput from '@/components/common/TextInput.vue'
import type { ProjectDocument } from '@/types/Document'

const props = defineProps<{
  modelValue: boolean
  document: ProjectDocument | null
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: { title: string }]
}>()

const form = reactive({ title: '' })
const errors = reactive({ title: '' })

watch(
  () => props.modelValue,
  (open) => {
    if (!open || !props.document) return
    form.title = props.document.title
    errors.title = ''
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  errors.title = form.title.trim() ? '' : 'Title is required'
  if (errors.title) return

  emit('confirm', { title: form.title.trim() })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="Edit Document" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <TextInput v-model="form.title" label="Document Title" required :error="errors.title" />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">Save Changes</BaseButton>
    </template>
  </BaseDialog>
</template>
