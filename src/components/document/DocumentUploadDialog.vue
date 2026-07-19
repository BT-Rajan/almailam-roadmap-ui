<script setup lang="ts">
import { computed, ref } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import type { DocumentType, ProjectDocument } from '@/types/Document'
import type { Project } from '@/types/Project'
import type { SelectOption } from '@/types/Ui'

const DOCUMENT_TYPE_OPTIONS: SelectOption[] = [
  { label: 'Drawing', value: 'Drawing' },
  { label: 'Report', value: 'Report' },
  { label: 'Contract', value: 'Contract' },
  { label: 'Quotation', value: 'Quotation' },
  { label: 'Municipality Form', value: 'Municipality Form' },
  { label: 'Calculation Sheet', value: 'Calculation Sheet' },
]

const props = defineProps<{
  modelValue: boolean
  projects: Project[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  upload: [document: ProjectDocument]
}>()

const title = ref('')
const documentType = ref<DocumentType | ''>('')
const projectId = ref('')
const selectedFile = ref<File>()
const titleError = ref<string>()

const projectOptions = computed<SelectOption[]>(() =>
  props.projects.map((project) => ({ label: project.projectName, value: project.id })),
)

const canSubmit = computed(
  () => title.value.trim().length > 0 && documentType.value.length > 0 && projectId.value.length > 0,
)

function resetForm(): void {
  title.value = ''
  documentType.value = ''
  projectId.value = ''
  selectedFile.value = undefined
  titleError.value = undefined
}

function closeDialog(): void {
  emit('update:modelValue', false)
  resetForm()
}

function submitUpload(): void {
  if (!canSubmit.value) {
    titleError.value = title.value.trim().length === 0 ? 'Document title is required' : undefined
    return
  }

  const newDocument: ProjectDocument = {
    id: `DOC-2026-${crypto.randomUUID().slice(0, 6).toUpperCase()}`,
    projectId: projectId.value,
    title: title.value.trim(),
    type: documentType.value as DocumentType,
    revision: 'Rev A',
    uploadedBy: 'You',
    uploadDate: new Date().toISOString().slice(0, 10),
    status: 'Draft',
    fileSize: selectedFile.value ? `${(selectedFile.value.size / 1024).toFixed(0)} KB` : '—',
  }

  emit('upload', newDocument)
  closeDialog()
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="Upload Document" size="md" @update:model-value="closeDialog">
    <div class="flex flex-col gap-4">
      <TextInput v-model="title" label="Document Title" placeholder="e.g. Structural Drawing" required :error="titleError" />

      <SelectBox v-model="projectId" label="Project" placeholder="Select project" :options="projectOptions" required />

      <SelectBox
        :model-value="documentType"
        label="Document Type"
        placeholder="Select type"
        :options="DOCUMENT_TYPE_OPTIONS"
        required
        @update:model-value="documentType = $event as DocumentType"
      />

      <FileUploader @select="selectedFile = $event" />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :disabled="!canSubmit" @click="submitUpload">Upload Document</BaseButton>
    </template>
  </BaseDialog>
</template>
