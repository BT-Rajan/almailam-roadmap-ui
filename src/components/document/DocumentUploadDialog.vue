<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import { useDocumentStore } from '@/stores/documentStore'
import { useToastStore } from '@/stores/toastStore'
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
  { label: 'Government Agreement', value: 'Government Agreement' },
]

const props = defineProps<{
  modelValue: boolean
  projects: Project[]
  // Pre-fills title/type/project when opened for a specific required
  // document (e.g. a permit checklist item) instead of a blank upload.
  initialTitle?: string
  initialDocumentType?: DocumentType
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  upload: [document: ProjectDocument]
}>()

const documentStore = useDocumentStore()
const toastStore = useToastStore()

const title = ref('')
const documentType = ref<DocumentType | ''>('')
const projectId = ref('')
const selectedFile = ref<File>()
const titleError = ref<string>()
const fileError = ref<string>()
const isUploading = ref(false)

const projectOptions = computed<SelectOption[]>(() =>
  props.projects.map((project) => ({ label: project.projectName, value: project.id })),
)

const canSubmit = computed(
  () =>
    title.value.trim().length > 0 &&
    documentType.value.length > 0 &&
    projectId.value.length > 0 &&
    Boolean(selectedFile.value),
)

function resetForm(): void {
  title.value = ''
  documentType.value = ''
  projectId.value = ''
  selectedFile.value = undefined
  titleError.value = undefined
  fileError.value = undefined
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (!isOpen) return
    if (props.initialTitle) title.value = props.initialTitle
    if (props.initialDocumentType) documentType.value = props.initialDocumentType
    if (props.projects.length === 1) projectId.value = props.projects[0].id
  },
)

function closeDialog(): void {
  if (isUploading.value) return
  emit('update:modelValue', false)
  resetForm()
}

async function submitUpload(): Promise<void> {
  titleError.value = title.value.trim().length === 0 ? 'Document title is required' : undefined
  fileError.value = selectedFile.value ? undefined : 'Please select a file to upload'
  if (!canSubmit.value) return

  isUploading.value = true
  try {
    const document = await documentStore.uploadDocument(
      selectedFile.value as File,
      projectId.value,
      title.value.trim(),
      documentType.value as DocumentType,
    )
    emit('upload', document)
    closeDialog()
  } catch (error) {
    toastStore.show(
      'error',
      'Upload failed',
      error instanceof Error && error.message ? error.message : 'Please try again.',
    )
  } finally {
    isUploading.value = false
  }
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="Upload Document" size="md" :closable="!isUploading" @update:model-value="closeDialog">
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

      <div class="flex flex-col gap-1.5">
        <FileUploader @select="selectedFile = $event" />
        <p v-if="fileError" class="text-xs text-danger-500">{{ fileError }}</p>
      </div>
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="isUploading" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :disabled="!canSubmit" :loading="isUploading" @click="submitUpload">Upload Document</BaseButton>
    </template>
  </BaseDialog>
</template>
