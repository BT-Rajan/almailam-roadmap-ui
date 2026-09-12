<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

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
  { label: 'Drawing', value: 'Drawing', labelKey: 'document.uploadDialog.typeDrawing' },
  { label: 'Report', value: 'Report', labelKey: 'document.uploadDialog.typeReport' },
  { label: 'Contract', value: 'Contract', labelKey: 'document.uploadDialog.typeContract' },
  { label: 'Quotation', value: 'Quotation', labelKey: 'document.uploadDialog.typeQuotation' },
  { label: 'Municipality Form', value: 'Municipality Form', labelKey: 'document.uploadDialog.typeMunicipalityForm' },
  { label: 'Calculation Sheet', value: 'Calculation Sheet', labelKey: 'document.uploadDialog.typeCalculationSheet' },
  { label: 'Government Agreement', value: 'Government Agreement', labelKey: 'document.uploadDialog.typeGovernmentAgreement' },
]

// Kept in sync with backend/app/core/file_storage.py's own
// ALLOWED_EXTENSIONS/MAX_UPLOAD_SIZE_MB -- catches an oversized or
// wrong-type file the instant it's picked, instead of only after the
// whole file has already uploaded over the network and the backend
// rejects it. FileUploader.vue already supported this (the New Client
// wizard's identification upload uses its own, narrower version), it
// just was never wired up here for ordinary document uploads.
const MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024
const ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.dwg', '.dxf', '.jpg', '.jpeg', '.png', '.tiff', '.tif', '.txt', '.csv']

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
const { t } = useI18n()

const title = ref('')
const documentType = ref<DocumentType | ''>('')
const projectId = ref('')
const selectedFile = ref<File>()
const titleError = ref<string>()
const projectError = ref<string>()
const documentTypeError = ref<string>()
const fileError = ref<string>()
const isUploading = ref(false)

const projectOptions = computed<SelectOption[]>(() =>
  props.projects.map((project) => ({ label: project.projectName, value: project.id })),
)

function resetForm(): void {
  title.value = ''
  documentType.value = ''
  projectId.value = ''
  selectedFile.value = undefined
  titleError.value = undefined
  projectError.value = undefined
  documentTypeError.value = undefined
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
  titleError.value = title.value.trim().length === 0 ? t('document.uploadDialog.titleRequired') : undefined
  projectError.value = projectId.value.length === 0 ? t('document.uploadDialog.projectRequired') : undefined
  documentTypeError.value = documentType.value.length === 0 ? t('document.uploadDialog.documentTypeRequired') : undefined
  fileError.value = selectedFile.value ? undefined : t('document.uploadDialog.fileRequired')
  if (titleError.value || projectError.value || documentTypeError.value || fileError.value) return

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
      t('common.uploadFailed'),
      error instanceof Error && error.message ? error.message : t('common.pleaseTryAgain'),
    )
  } finally {
    isUploading.value = false
  }
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="t('document.uploadDialog.title')" size="md" :closable="!isUploading" @update:model-value="closeDialog">
    <div class="flex flex-col gap-4">
      <TextInput
        v-model="title"
        :label="t('document.uploadDialog.documentTitle')"
        :placeholder="t('document.uploadDialog.documentTitlePlaceholder')"
        required
        :error="titleError"
      />

      <SelectBox v-model="projectId" :label="t('document.uploadDialog.project')" :placeholder="t('document.uploadDialog.projectPlaceholder')" :options="projectOptions" required :error="projectError" />

      <SelectBox
        :model-value="documentType"
        :label="t('document.uploadDialog.documentType')"
        :placeholder="t('document.uploadDialog.documentTypePlaceholder')"
        :options="DOCUMENT_TYPE_OPTIONS"
        required
        :error="documentTypeError"
        @update:model-value="documentType = $event as DocumentType"
      />

      <div class="flex flex-col gap-1.5">
        <FileUploader
          :max-size-bytes="MAX_UPLOAD_SIZE_BYTES"
          :allowed-extensions="ALLOWED_EXTENSIONS"
          @select="selectedFile = $event"
          @error="fileError = $event"
        />
        <p v-if="fileError" class="text-xs text-danger-500">{{ fileError }}</p>
      </div>
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="isUploading" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="isUploading" @click="submitUpload">{{ t('document.uploadDialog.uploadDocument') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
