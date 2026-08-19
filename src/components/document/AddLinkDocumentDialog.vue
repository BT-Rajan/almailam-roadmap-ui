<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useProjectLinkDocumentStore } from '@/stores/projectLinkDocumentStore'
import { useToastStore } from '@/stores/toastStore'
import type { ProjectLinkDocument, ProjectLinkDocumentCategory } from '@/types/Document'
import type { SelectOption } from '@/types/Ui'

const CATEGORY_OPTIONS: SelectOption[] = [
  { label: 'Property Documents', value: 'Property' },
  { label: 'Government Documents', value: 'Government' },
  { label: 'Others', value: 'Others' },
]

const props = defineProps<{
  modelValue: boolean
  projectId: string
  // Preselects and locks the category when opened from a specific
  // section's "Add Document" button; left blank when opened generically.
  category?: ProjectLinkDocumentCategory
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  add: [document: ProjectLinkDocument]
}>()

const linkDocumentStore = useProjectLinkDocumentStore()
const toastStore = useToastStore()

const name = ref('')
const path = ref('')
const selectedCategory = ref<ProjectLinkDocumentCategory | ''>('')
const nameError = ref<string>()
const pathError = ref<string>()
const isSaving = ref(false)

watch(
  () => props.modelValue,
  (open) => {
    if (open) selectedCategory.value = props.category ?? ''
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
  <BaseDialog :model-value="modelValue" title="Add Document" size="md" :closable="!isSaving" @update:model-value="closeDialog">
    <div class="flex flex-col gap-4">
      <SelectBox
        :model-value="selectedCategory"
        label="Category"
        placeholder="Select category"
        :options="CATEGORY_OPTIONS"
        required
        :disabled="Boolean(props.category)"
        @update:model-value="selectedCategory = $event as ProjectLinkDocumentCategory"
      />

      <TextInput v-model="name" label="Document Name" placeholder="e.g. Title Deed" required :error="nameError" />

      <TextInput
        v-model="path"
        label="Document Path / Link"
        placeholder="e.g. https://drive.example.com/... or \\server\share\file.pdf"
        required
        :error="pathError"
      />
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="isSaving" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :disabled="!canSubmit" :loading="isSaving" @click="submitAdd">Add Document</BaseButton>
    </template>
  </BaseDialog>
</template>
