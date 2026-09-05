<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useProjectLinkDocumentStore } from '@/stores/projectLinkDocumentStore'
import { useToastStore } from '@/stores/toastStore'
import type { ProjectLinkDocument, ProjectLinkDocumentCategory } from '@/types/Document'
import type { SelectOption } from '@/types/Ui'

const CATEGORY_OPTIONS: SelectOption[] = [
  { label: 'Property Documents', value: 'Property', labelKey: 'document.addLinkDialog.categoryProperty' },
  { label: 'Government Documents', value: 'Government', labelKey: 'document.addLinkDialog.categoryGovernment' },
  { label: 'Others', value: 'Others', labelKey: 'document.addLinkDialog.categoryOthers' },
  { label: 'Project Closure', value: 'Project Closure', labelKey: 'document.addLinkDialog.categoryProjectClosure' },
]

const props = defineProps<{
  modelValue: boolean
  projectId: string
  // Preselects and locks the category when opened from a specific
  // section's "Add Document" button; left blank when opened generically.
  category?: ProjectLinkDocumentCategory
  // Pre-fills the name when opened for a specific required document (e.g.
  // a permit checklist item) instead of a blank entry.
  initialName?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  add: [document: ProjectLinkDocument]
}>()

const linkDocumentStore = useProjectLinkDocumentStore()
const toastStore = useToastStore()
const { t } = useI18n()

const name = ref('')
const path = ref('')
const selectedCategory = ref<ProjectLinkDocumentCategory | ''>('')
const nameError = ref<string>()
const pathError = ref<string>()
const isSaving = ref(false)

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      selectedCategory.value = props.category ?? ''
      if (props.initialName) name.value = props.initialName
    }
  },
)

const canSubmit = computed(
  () => name.value.trim().length > 0 && path.value.trim().length > 0 && selectedCategory.value.length > 0,
)

function resetForm(): void {
  name.value = ''
  path.value = ''
  selectedCategory.value = props.category ?? ''
  nameError.value = undefined
  pathError.value = undefined
}

function closeDialog(): void {
  if (isSaving.value) return
  emit('update:modelValue', false)
  resetForm()
}

async function submitAdd(): Promise<void> {
  nameError.value = name.value.trim().length === 0 ? 'Document name is required' : undefined
  pathError.value = path.value.trim().length === 0 ? 'Document path or link is required' : undefined
  if (!canSubmit.value) return

  isSaving.value = true
  try {
    const document = await linkDocumentStore.addDocument(
      props.projectId,
      selectedCategory.value as ProjectLinkDocumentCategory,
      name.value.trim(),
      path.value.trim(),
    )
    toastStore.show('success', 'Document added', `${document.name} was added.`)
    emit('add', document)
    closeDialog()
  } catch (error) {
    toastStore.show(
      'error',
      'Failed to add document',
      error instanceof Error && error.message ? error.message : 'Please try again.',
    )
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="t('document.addLinkDialog.title')" size="md" :closable="!isSaving" @update:model-value="closeDialog">
    <div class="flex flex-col gap-4">
      <SelectBox
        :model-value="selectedCategory"
        :label="t('document.addLinkDialog.category')"
        :placeholder="t('document.addLinkDialog.categoryPlaceholder')"
        :options="CATEGORY_OPTIONS"
        required
        :disabled="Boolean(props.category)"
        @update:model-value="selectedCategory = $event as ProjectLinkDocumentCategory"
      />

      <TextInput
        v-model="name"
        :label="t('document.addLinkDialog.documentName')"
        :placeholder="t('document.addLinkDialog.documentNamePlaceholder')"
        required
        :error="nameError"
      />

      <TextInput
        v-model="path"
        :label="t('document.addLinkDialog.documentPathLink')"
        :placeholder="t('document.addLinkDialog.documentPathLinkPlaceholder')"
        required
        :error="pathError"
      />
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="isSaving" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :disabled="!canSubmit" :loading="isSaving" @click="submitAdd">{{ t('document.addLinkDialog.addDocument') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
