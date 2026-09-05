<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import TextInput from '@/components/common/TextInput.vue'
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

const { t } = useI18n()

const title = ref('')
const date = ref('')
const link = ref('')
const titleError = ref<string>()
const linkError = ref<string>()

function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    titleError.value = undefined
    linkError.value = undefined
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

function isValidUrl(value: string): boolean {
  try {
    const parsed = new URL(value)
    return parsed.protocol === 'http:' || parsed.protocol === 'https:'
  } catch {
    return false
  }
}

function handleSave(): void {
  titleError.value = title.value.trim() ? undefined : 'Document name is required'
  const trimmedLink = link.value.trim()
  linkError.value = !trimmedLink ? 'Link is required' : !isValidUrl(trimmedLink) ? 'Enter a valid http(s) link' : undefined
  if (titleError.value || linkError.value) return

  emit('save', { title: title.value.trim(), date: date.value, link: trimmedLink, file: undefined })
}

function closeDialog(): void {
  if (props.isSaving) return
  emit('update:modelValue', false)
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="document ? t('document.designDocumentDialog.editTitle') : t('document.designDocumentDialog.addTitle')"
    size="md"
    :closable="!isSaving"
    @update:model-value="closeDialog"
  >
    <div class="flex flex-col gap-4">
      <TextInput
        v-model="title"
        :label="t('document.designDocumentDialog.document')"
        :placeholder="t('document.designDocumentDialog.documentPlaceholder')"
        required
        :error="titleError"
      />
      <DatePicker v-model="date" :label="t('document.designDocumentDialog.date')" required />
      <TextInput v-model="link" :label="t('document.designDocumentDialog.link')" placeholder="https://..." required :error="linkError" />
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="isSaving" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="isSaving" @click="handleSave">{{ t('common.save') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
