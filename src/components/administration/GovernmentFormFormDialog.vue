<script setup lang="ts">
import { Plus, Trash2, Upload } from '@lucide/vue'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { FORM_CATEGORY_OPTIONS, FORM_LANGUAGE_OPTIONS } from '@/constants/governmentFormOptions'
import type { FormInput } from '@/services/governmentFormService'
import { useGovernmentFormStore } from '@/stores/governmentFormStore'
import { useToastStore } from '@/stores/toastStore'
import type {
  GovernmentAuthority,
  GovernmentForm,
  GovernmentFormCategory,
  GovernmentFormField,
  GovernmentFormLanguage,
} from '@/types/Government'
import type { ServiceCatalogItem } from '@/types/ServiceCatalog'
import type { SelectOption } from '@/types/Ui'

interface Props {
  modelValue: boolean
  form?: GovernmentForm
  authorities: GovernmentAuthority[]
  services: ServiceCatalogItem[]
  saving?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  form: undefined,
  saving: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [input: FormInput]
}>()

const governmentFormStore = useGovernmentFormStore()
const toastStore = useToastStore()
const { t } = useI18n()

type FormDraft = Omit<FormInput, 'template'> & { requiredDocumentsText: string; template: string }

function emptyDraft(): FormDraft {
  return {
    authorityId: props.authorities[0]?.id ?? '',
    formCode: '',
    title: '',
    version: 'v1.0',
    language: 'English',
    category: 'Building Permit',
    description: '',
    requiredDocuments: [],
    requiredDocumentsText: '',
    lastUpdated: new Date().toISOString().slice(0, 10),
    status: 'Active',
    template: '',
    serviceTags: [],
    fields: [],
  }
}

const FIELD_TYPE_OPTIONS: SelectOption[] = [
  { label: 'Text', value: 'text', labelKey: 'administration.governmentFormDialog.fieldType.text' },
  { label: 'Dropdown', value: 'select', labelKey: 'administration.governmentFormDialog.fieldType.dropdown' },
  { label: 'Radio buttons', value: 'radio', labelKey: 'administration.governmentFormDialog.fieldType.radioButtons' },
]

function addField(): void {
  draft.value.fields = [...draft.value.fields, { token: '', label: '', type: 'text', options: [] }]
}

function removeField(index: number): void {
  draft.value.fields = draft.value.fields.filter((_, i) => i !== index)
}

function optionsText(field: GovernmentFormField): string {
  return field.options.join('\n')
}

function setOptionsText(index: number, text: string): void {
  draft.value.fields[index]!.options = text
    .split('\n')
    .map((line) => line.trim())
    .filter((line) => line.length > 0)
}

const isUploadingSample = ref(false)
// Local display value so the "currently attached" filename updates
// immediately after a successful upload -- props.form itself won't
// reflect it until GovernmentFormsPanel.vue's own list refreshes.
const uploadedSampleFileName = ref<string | null>(null)

async function handleSampleFileSelected(event: Event): Promise<void> {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file || !props.form) return
  isUploadingSample.value = true
  try {
    await governmentFormStore.uploadSampleFile(props.form.id, file)
    uploadedSampleFileName.value = file.name
    toastStore.show('success', 'Sample file uploaded', `${file.name} was attached to this form.`)
  } catch (error) {
    toastStore.show('error', 'Upload failed', error instanceof Error ? error.message : 'Please try again.')
  } finally {
    isUploadingSample.value = false
    ;(event.target as HTMLInputElement).value = ''
  }
}

const draft = ref(emptyDraft())
const errors = ref<Record<string, string>>({})

const authorityOptions = computed<SelectOption[]>(() =>
  props.authorities.map((authority) => ({ label: authority.name, value: authority.id })),
)

function isServiceTagged(serviceName: string): boolean {
  return draft.value.serviceTags.includes(serviceName)
}

function toggleServiceTag(serviceName: string): void {
  draft.value.serviceTags = isServiceTagged(serviceName)
    ? draft.value.serviceTags.filter((tag) => tag !== serviceName)
    : [...draft.value.serviceTags, serviceName]
}

watch(
  () => [props.modelValue, props.form] as const,
  ([isOpen, existingForm]) => {
    if (!isOpen) return
    draft.value = existingForm
      ? {
          ...existingForm,
          requiredDocumentsText: existingForm.requiredDocuments.join('\n'),
          template: existingForm.template ?? '',
          serviceTags: existingForm.serviceTags ?? [],
        }
      : emptyDraft()
    errors.value = {}
    uploadedSampleFileName.value = null
  },
  { immediate: true },
)

function validate(): boolean {
  errors.value = {}
  if (!draft.value.title.trim()) errors.value.title = 'Form title is required'
  if (!draft.value.formCode.trim()) errors.value.formCode = 'Form code is required'
  if (!draft.value.authorityId) errors.value.authorityId = 'Please select an authority'
  if (!draft.value.description.trim()) errors.value.description = 'Description is required'
  return Object.keys(errors.value).length === 0
}

function handleSave(): void {
  if (!validate()) return

  const input: FormInput = {
    authorityId: draft.value.authorityId,
    formCode: draft.value.formCode.trim(),
    title: draft.value.title.trim(),
    version: draft.value.version.trim() || 'v1.0',
    language: draft.value.language as GovernmentFormLanguage,
    category: draft.value.category as GovernmentFormCategory,
    description: draft.value.description,
    requiredDocuments: draft.value.requiredDocumentsText
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0),
    lastUpdated: draft.value.lastUpdated,
    status: draft.value.status,
    previewUrl: draft.value.previewUrl,
    template: draft.value.template?.trim() || undefined,
    serviceTags: draft.value.serviceTags,
    fields: draft.value.fields
      .filter((field) => field.token.trim().length > 0)
      .map((field) => ({ ...field, token: field.token.trim(), label: field.label.trim() || field.token.trim() })),
  }

  emit('save', input)
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="form ? t('administration.governmentFormDialog.editTitle') : t('administration.governmentFormDialog.addTitle')"
    size="lg"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="flex flex-col gap-4">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <TextInput v-model="draft.title" :label="t('administration.governmentFormDialog.formTitle')" :error="errors.title" required />
        <TextInput
          v-model="draft.formCode"
          :label="t('administration.governmentFormDialog.formCode')"
          :placeholder="t('administration.governmentFormDialog.formCodePlaceholder')"
          :error="errors.formCode"
          required
        />
      </div>

      <SelectBox
        v-model="draft.authorityId"
        :label="t('administration.governmentFormDialog.authority')"
        :options="authorityOptions"
        :error="errors.authorityId"
        required
      />

      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
        <SelectBox v-model="draft.category" :label="t('administration.governmentFormDialog.category')" :options="FORM_CATEGORY_OPTIONS" />
        <SelectBox v-model="draft.language" :label="t('administration.governmentFormDialog.language')" :options="FORM_LANGUAGE_OPTIONS" />
        <TextInput v-model="draft.version" :label="t('administration.governmentFormDialog.version')" :placeholder="t('administration.governmentFormDialog.versionPlaceholder')" />
      </div>

      <DatePicker v-model="draft.lastUpdated" :label="t('administration.governmentFormDialog.lastUpdated')" />
      <TextArea v-model="draft.description" :label="t('administration.governmentFormDialog.description')" :rows="3" :error="errors.description" required />
      <TextArea
        v-model="draft.requiredDocumentsText"
        :label="t('administration.governmentFormDialog.requiredDocuments')"
        :hint="t('administration.governmentFormDialog.requiredDocumentsHint')"
        :rows="4"
      />

      <TextArea
        v-model="draft.template"
        :label="t('administration.governmentFormDialog.templateContent')"
        :hint="t('administration.governmentFormDialog.templateContentHint')"
        :rows="8"
      />

      <div class="flex flex-col gap-3 rounded-lg border border-border-light p-4">
        <div>
          <p class="text-sm font-medium text-text-secondary">{{ t('administration.governmentFormDialog.fieldsSectionTitle') }}</p>
          <p class="text-xs text-text-muted">
            {{ t('administration.governmentFormDialog.fieldsHintPrefix') }}
            <code v-pre>{{plotArea}}</code>
            {{ t('administration.governmentFormDialog.fieldsHintSuffix') }}
          </p>
        </div>

        <div v-for="(field, index) in draft.fields" :key="index" class="flex flex-col gap-2 rounded-lg border border-border-light p-3">
          <div class="flex items-start gap-2">
            <TextInput v-model="field.token" :placeholder="t('administration.governmentFormDialog.fieldTokenPlaceholder')" class="flex-1" />
            <TextInput v-model="field.label" :placeholder="t('administration.governmentFormDialog.fieldLabelPlaceholder')" class="flex-1" />
            <SelectBox v-model="field.type" :options="FIELD_TYPE_OPTIONS" class="w-40" />
            <IconButton :icon="Trash2" :label="t('administration.governmentFormDialog.removeField')" size="sm" variant="danger" @click="removeField(index)" />
          </div>
          <TextArea
            v-if="field.type === 'select' || field.type === 'radio'"
            :model-value="optionsText(field)"
            :placeholder="t('administration.governmentFormDialog.fieldOptionsPlaceholder')"
            :rows="3"
            @update:model-value="setOptionsText(index, $event)"
          />
        </div>

        <BaseButton variant="secondary" size="sm" :icon="Plus" @click="addField">{{ t('administration.governmentFormDialog.addField') }}</BaseButton>
      </div>

      <div v-if="form" class="flex flex-col gap-2 rounded-lg border border-border-light p-4">
        <p class="text-sm font-medium text-text-secondary">{{ t('administration.governmentFormDialog.sampleFormTitle') }}</p>
        <p class="text-xs text-text-muted">
          {{ t('administration.governmentFormDialog.sampleFormHint') }}
        </p>
        <p v-if="uploadedSampleFileName ?? form.sampleFileName" class="text-xs text-text-secondary">
          {{ t('administration.governmentFormDialog.currentlyAttached', { name: uploadedSampleFileName ?? form.sampleFileName }) }}
        </p>
        <label class="inline-flex w-fit cursor-pointer items-center gap-2 rounded-lg border border-border-default bg-bg-card px-3 py-1.5 text-sm font-medium text-text-secondary hover:bg-bg-hover">
          <Upload class="h-4 w-4" />
          {{ isUploadingSample ? t('administration.governmentFormDialog.uploading') : t('administration.governmentFormDialog.uploadSample') }}
          <input type="file" class="hidden" :disabled="isUploadingSample" @change="handleSampleFileSelected" />
        </label>
      </div>

      <div>
        <p class="mb-1.5 text-sm font-medium text-text-secondary">{{ t('administration.governmentFormDialog.taggedServicesTitle') }}</p>
        <p class="mb-2 text-xs text-text-muted">
          {{ t('administration.governmentFormDialog.taggedServicesHint') }}
        </p>
        <EmptyState
          v-if="services.length === 0"
          :title="t('administration.governmentFormDialog.noServicesTitle')"
          :description="t('administration.governmentFormDialog.noServicesDescription')"
        />
        <div v-else class="grid grid-cols-1 gap-1.5 rounded-lg border border-border-light p-3 tablet:grid-cols-2">
          <Checkbox
            v-for="service in services"
            :key="service.id"
            :model-value="isServiceTagged(service.name)"
            :label="service.name"
            @update:model-value="toggleServiceTag(service.name)"
          />
        </div>
      </div>
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="saving" @click="emit('update:modelValue', false)">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="saving" @click="handleSave">{{ t('administration.governmentFormDialog.saveForm') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
