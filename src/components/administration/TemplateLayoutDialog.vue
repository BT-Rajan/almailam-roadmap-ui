<script setup lang="ts">
import { Trash2 } from '@lucide/vue'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import IconButton from '@/components/common/IconButton.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import { useDocumentTemplateStore } from '@/stores/documentTemplateStore'
import { useToastStore } from '@/stores/toastStore'
import type { DocumentTemplate } from '@/types/DocumentTemplate'
import type { SelectOption } from '@/types/Ui'

interface Props {
  modelValue: boolean
  template: DocumentTemplate | undefined
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const store = useDocumentTemplateStore()
const toastStore = useToastStore()
const { t } = useI18n()

const ORIENTATION_OPTIONS: SelectOption[] = [
  { label: t('administration.documentTemplates.portrait'), value: 'Portrait' },
  { label: t('administration.documentTemplates.landscape'), value: 'Landscape' },
]

const orientation = ref<'Portrait' | 'Landscape'>('Portrait')
const marginTopMm = ref(25)
const marginRightMm = ref(20)
const marginBottomMm = ref(25)
const marginLeftMm = ref(20)
const isSavingLayout = ref(false)
const isUploadingBackground = ref(false)
const isRemovingBackground = ref(false)

// Reset the form's local copy every time a different template is opened
// (or its stored values change under us, e.g. after a save elsewhere) --
// the dialog edits a draft copy, not the store directly, so Cancel/close
// without Save leaves the template untouched.
watch(
  () => props.template,
  (template) => {
    orientation.value = template?.orientation ?? 'Portrait'
    marginTopMm.value = template?.marginTopMm ?? 25
    marginRightMm.value = template?.marginRightMm ?? 20
    marginBottomMm.value = template?.marginBottomMm ?? 25
    marginLeftMm.value = template?.marginLeftMm ?? 20
  },
  { immediate: true },
)

function close(): void {
  emit('update:modelValue', false)
}

async function handleBackgroundSelect(file: File | undefined): Promise<void> {
  if (!file || !props.template) return
  isUploadingBackground.value = true
  try {
    await store.uploadBackground(props.template.id, file)
    toastStore.show('success', t('administration.documentTemplates.backgroundUploadedTitle'), t('administration.documentTemplates.backgroundUploadedDescription'))
  } catch (error) {
    toastStore.show('error', t('common.uploadFailed'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isUploadingBackground.value = false
  }
}

async function handleRemoveBackground(): Promise<void> {
  if (!props.template) return
  isRemovingBackground.value = true
  try {
    await store.removeBackground(props.template.id)
  } catch (error) {
    toastStore.show('error', t('common.somethingWentWrong'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isRemovingBackground.value = false
  }
}

async function saveLayout(): Promise<void> {
  if (!props.template) return
  isSavingLayout.value = true
  try {
    await store.updateLayout(props.template.id, {
      orientation: orientation.value,
      marginTopMm: marginTopMm.value,
      marginRightMm: marginRightMm.value,
      marginBottomMm: marginBottomMm.value,
      marginLeftMm: marginLeftMm.value,
    })
    toastStore.show('success', t('administration.documentTemplates.layoutSavedTitle'), t('administration.documentTemplates.layoutSavedDescription'))
    close()
  } catch (error) {
    toastStore.show('error', t('common.somethingWentWrong'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isSavingLayout.value = false
  }
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="t('administration.documentTemplates.layoutDialogTitle')" size="sm" @update:model-value="close">
    <div class="flex flex-col gap-5">
      <div class="flex flex-col gap-2">
        <p class="text-xs font-semibold uppercase tracking-wide text-text-muted">{{ t('administration.documentTemplates.letterhead') }}</p>
        <p class="text-xs text-text-muted">{{ t('administration.documentTemplates.letterheadHint') }}</p>
        <div v-if="template?.backgroundFilename" class="flex items-center justify-between gap-3 rounded-lg border border-border-light bg-bg-secondary px-3 py-2">
          <span class="truncate text-sm text-text-primary">{{ template.backgroundFilename }}</span>
          <IconButton
            :icon="Trash2"
            :label="t('administration.documentTemplates.removeBackground')"
            variant="danger"
            size="sm"
            :disabled="isRemovingBackground"
            @click="handleRemoveBackground"
          />
        </div>
        <FileUploader accept=".png,.jpg,.jpeg" :hint="t('administration.documentTemplates.letterheadUploadHint')" @select="handleBackgroundSelect" />
        <p v-if="isUploadingBackground" class="text-xs text-text-muted">{{ t('common.uploading') }}</p>
      </div>

      <SelectBox v-model="orientation" :label="t('administration.documentTemplates.orientation')" :options="ORIENTATION_OPTIONS" />

      <div class="flex flex-col gap-2">
        <p class="text-xs font-semibold uppercase tracking-wide text-text-muted">{{ t('administration.documentTemplates.margins') }}</p>
        <div class="grid grid-cols-2 gap-3">
          <NumberInput v-model="marginTopMm" :label="t('administration.documentTemplates.marginTop')" :min="0" :max="60" />
          <NumberInput v-model="marginRightMm" :label="t('administration.documentTemplates.marginRight')" :min="0" :max="60" />
          <NumberInput v-model="marginBottomMm" :label="t('administration.documentTemplates.marginBottom')" :min="0" :max="60" />
          <NumberInput v-model="marginLeftMm" :label="t('administration.documentTemplates.marginLeft')" :min="0" :max="60" />
        </div>
      </div>
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="isSavingLayout" @click="close">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="isSavingLayout" @click="saveLayout">{{ t('common.save') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
