<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import TextInput from '@/components/common/TextInput.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import type { ProjectDocument } from '@/types/Document'

const props = defineProps<{
  modelValue: boolean
  // null means "add" -- otherwise the row being edited.
  document: ProjectDocument | null
  isSaving?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [payload: { title: string; date: string; link: string; file: File | undefined }]
}>()

const title = ref('')
const date = ref('')
const link = ref('')
const selectedFile = ref<File>()
const titleError = ref<string>()
const fileOrLinkError = ref<string>()

function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    titleError.value = undefined
    fileOrLinkError.value = undefined
    selectedFile.value = undefined
    if (props.document) {
      title.value = props.document.title
      date.value = props.document.uploadDate
      link.value = props.document.externalLink ?? ''
    } else {
      title.value = ''
      date.value = todayIso()
      link.value = ''
    }
  },
)

const hasExistingFile = computed(() => Boolean(props.document?.originalFilename))

function handleSave(): void {
  titleError.value = title.value.trim() ? undefined : 'Document name is required'
  fileOrLinkError.value =
    selectedFile.value || link.value.trim() || hasExistingFile.value ? undefined : 'Provide a file, a link, or both'
  if (titleError.value || fileOrLinkError.value) return

  emit('save', { title: title.value.trim(), date: date.value, link: link.value.trim(), file: selectedFile.value })
}

function closeDialog(): void {
  if (props.isSaving) return
  emit('update:modelValue', false)
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="document ? 'Edit Document' : 'Add Document'"
    size="md"
    :closable="!isSaving"
    @update:model-value="closeDialog"
  >
    <div class="flex flex-col gap-4">
      <TextInput v-model="title" label="Document" placeholder="e.g. Structural Drawing R1" required :error="titleError" />
      <DatePicker v-model="date" label="Date" required />
      <TextInput v-model="link" label="Link (optional)" placeholder="https://..." />
      <div class="flex flex-col gap-1.5">
        <FileUploader
          :hint="hasExistingFile ? `Replace ${document?.originalFilename}` : 'PDF, Word, Excel, DWG or image files'"
          @select="selectedFile = $event"
        />
        <p v-if="fileOrLinkError" class="text-xs text-danger-500">{{ fileOrLinkError }}</p>
      </div>
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="isSaving" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="isSaving" @click="handleSave">Save</BaseButton>
    </template>
  </BaseDialog>
</template>
