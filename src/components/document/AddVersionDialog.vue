<script setup lang="ts">
import { ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import TextArea from '@/components/common/TextArea.vue'
import FileUploader from '@/components/document/FileUploader.vue'

const props = defineProps<{
  modelValue: boolean
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: { file: File; notes?: string }]
}>()

const selectedFile = ref<File>()
const notes = ref('')
const fileError = ref<string>()

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    selectedFile.value = undefined
    notes.value = ''
    fileError.value = undefined
  },
)

function closeDialog(): void {
  if (props.loading) return
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  fileError.value = selectedFile.value ? undefined : 'Please select a file to upload'
  if (!selectedFile.value) return
  emit('confirm', { file: selectedFile.value, notes: notes.value.trim() || undefined })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="Add New Version" size="md" :closable="!loading" @update:model-value="closeDialog">
    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-1.5">
        <FileUploader @select="selectedFile = $event" />
        <p v-if="fileError" class="text-xs text-danger-500">{{ fileError }}</p>
      </div>
      <TextArea v-model="notes" label="Notes" placeholder="What changed in this revision?" :rows="3" />
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="loading" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">Upload New Version</BaseButton>
    </template>
  </BaseDialog>
</template>
