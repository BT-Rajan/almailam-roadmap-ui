<script setup lang="ts">
import { computed, ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import TextInput from '@/components/common/TextInput.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import { useKnowledgeStore } from '@/stores/knowledgeStore'
import { useToastStore } from '@/stores/toastStore'
import type { KnowledgeDocument } from '@/types/Knowledge'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  upload: [document: KnowledgeDocument]
}>()

const knowledgeStore = useKnowledgeStore()
const toastStore = useToastStore()

const title = ref('')
const selectedFile = ref<File>()
const fileError = ref<string>()

const canSubmit = computed(() => Boolean(selectedFile.value))

function resetForm(): void {
  title.value = ''
  selectedFile.value = undefined
  fileError.value = undefined
}

function closeDialog(): void {
  if (knowledgeStore.isUploading) return
  emit('update:modelValue', false)
  resetForm()
}

async function submitUpload(): Promise<void> {
  fileError.value = selectedFile.value ? undefined : 'Please select a file to upload'
  if (!canSubmit.value) return

  try {
    const document = await knowledgeStore.uploadDocument(selectedFile.value as File, title.value)
    emit('upload', document)
    closeDialog()
  } catch (error) {
    toastStore.show(
      'error',
      'Upload failed',
      error instanceof Error && error.message ? error.message : 'Please try again.',
    )
  }
}
</script>

<template>
  <BaseDialog
    :model-value="props.modelValue"
    title="Upload Knowledgebase Document"
    size="md"
    :closable="!knowledgeStore.isUploading"
    @update:model-value="closeDialog"
  >
    <div class="flex flex-col gap-4">
      <p class="text-sm text-text-muted">
        The document's text is extracted and used to ground answers on the Knowledge Base page. Only the
        text-layer content of the file is used -- a scanned/image-only PDF with no selectable text can't be
        answered from.
      </p>

      <TextInput v-model="title" label="Title (optional)" placeholder="Defaults to the file name" />

      <div class="flex flex-col gap-1.5">
        <FileUploader
          accept=".pdf,.docx,.txt"
          hint="PDF, Word (.docx), or plain text (.txt)"
          :allowed-extensions="['.pdf', '.docx', '.txt']"
          @select="selectedFile = $event"
          @error="fileError = $event"
        />
        <p v-if="fileError" class="text-xs text-danger-500">{{ fileError }}</p>
      </div>
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="knowledgeStore.isUploading" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :disabled="!canSubmit" :loading="knowledgeStore.isUploading" @click="submitUpload">Upload</BaseButton>
    </template>
  </BaseDialog>
</template>
