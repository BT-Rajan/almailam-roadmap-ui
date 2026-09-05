<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import TextArea from '@/components/common/TextArea.vue'
import FileUploader from '@/components/document/FileUploader.vue'

const props = defineProps<{
  modelValue: boolean
  loading?: boolean
}>()

const { t } = useI18n()

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
  <BaseDialog :model-value="modelValue" :title="t('document.addVersionDialog.title')" size="md" :closable="!loading" @update:model-value="closeDialog">
    <div class="flex flex-col gap-4">
      <div class="flex flex-col gap-1.5">
        <FileUploader @select="selectedFile = $event" />
        <p v-if="fileError" class="text-xs text-danger-500">{{ fileError }}</p>
      </div>
      <TextArea v-model="notes" :label="t('document.addVersionDialog.notes')" :placeholder="t('document.addVersionDialog.notesPlaceholder')" :rows="3" />
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="loading" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">{{ t('document.addVersionDialog.uploadNewVersion') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
