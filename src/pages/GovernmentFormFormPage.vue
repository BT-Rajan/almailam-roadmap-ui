<script setup lang="ts">
import { ArrowLeft, ArrowRight, Plus, Trash2, Upload } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import IconButton from '@/components/common/IconButton.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useLocale } from '@/composables/useLocale'
import { FORM_CATEGORY_OPTIONS, FORM_LANGUAGE_OPTIONS } from '@/constants/governmentFormOptions'
import { ROUTE_NAMES } from '@/constants/routeNames'
import type { FormInput } from '@/services/governmentFormService'
import { useGovernmentFormStore } from '@/stores/governmentFormStore'
import { useServiceCatalogStore } from '@/stores/serviceCatalogStore'
import { useToastStore } from '@/stores/toastStore'
import type { GovernmentFormCategory, GovernmentFormField, GovernmentFormLanguage } from '@/types/Government'
import type { SelectOption } from '@/types/Ui'

// Replaces GovernmentFormFormDialog.vue's modal -- a dedicated route
// (/government/forms/:formId), same treatment as
// ADMIN_USER_FORM/ADMIN_SCHEDULED_REPORT_FORM: ':formId' is 'new' or a
// real id, and the page decides create vs edit itself from whether
// that id resolves to an existing form.

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isRtl } = useLocale()
const governmentFormStore = useGovernmentFormStore()
const serviceCatalogStore = useServiceCatalogStore()
const toastStore = useToastStore()

const backIcon = computed(() => (isRtl.value ? ArrowRight : ArrowLeft))
const formId = computed(() => route.params.formId as string)
const isCreateMode = computed(() => formId.value === 'new')

function goBack(): void {
  router.push({ name: ROUTE_NAMES.GOVERNMENT_FORMS })
}

const isLoading = ref(true)
async function loadData(): Promise<void> {
  isLoading.value = true
  await Promise.all([
    governmentFormStore.forms.length === 0 ? governmentFormStore.loadForms() : Promise.resolve(),
    serviceCatalogStore.services.length === 0 ? serviceCatalogStore.loadServices() : Promise.resolve(),
  ])
  isLoading.value = false
}
onMounted(loadData)

const existingForm = computed(() =>
  isCreateMode.value ? undefined : governmentFormStore.forms.find((form) => form.id === formId.value),
)

// Set only when this page was opened from one authority's own forms
// view (GovernmentFormLibraryPanel.vue's "Add Form" button) -- just a
// default, not a lock: the admin can still change it, same as that
// panel's own dialogAuthorities reordering only ever pre-selected the
// authority being viewed rather than restricting the list to it.
const queryAuthorityId = computed(() => {
  const value = route.query.authorityId
  return typeof value === 'string' ? value : undefined
})

type FormDraft = Omit<FormInput, 'template'> & { requiredDocumentsText: string; template: string }

function emptyDraft(): FormDraft {
  return {
    authorityId: queryAuthorityId.value ?? governmentFormStore.authorities[0]?.id ?? '',
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

// Passed as a named i18n param (never written directly inside a
// translated string) -- see templateContentHint's own comment for why.
const TEMPLATE_TOKEN_EXAMPLES = '{{token}}, e.g. {{clientName}}, {{projectName}}, {{projectAddress}}, {{companyName}}, {{engineerName}}, {{date}}'

const FIELD_TYPE_OPTIONS: SelectOption[] = [
  { label: 'Text', value: 'text', labelKey: 'administration.governmentFormDialog.fieldType.text' },
  { label: 'Dropdown', value: 'select', labelKey: 'administration.governmentFormDialog.fieldType.dropdown' },
  { label: 'Radio buttons', value: 'radio', labelKey: 'administration.governmentFormDialog.fieldType.radioButtons' },
]

const draft = ref(emptyDraft())
const errors = ref<Record<string, string>>({})

// Seeds once loading finishes (from the existing form when editing,
// blank otherwise) -- guarded so a later reactive update (e.g. another
// tab saving a change to the same form list) doesn't silently discard
// in-progress edits.
const isFormSeeded = ref(false)
watch(
  () => [isLoading.value, existingForm.value] as const,
  ([loading, form]) => {
    if (loading || isFormSeeded.value) return
    draft.value = form
      ? { ...form, requiredDocumentsText: form.requiredDocuments.join('\n'), template: form.template ?? '', serviceTags: form.serviceTags ?? [] }
      : emptyDraft()
    isFormSeeded.value = true
    validate()
  },
  { immediate: true },
)
watch(draft, validate, { deep: true })

function validate(): boolean {
  errors.value = {}
  if (!draft.value.title.trim()) errors.value.title = t('administration.governmentFormDialog.titleRequired')
  if (!draft.value.formCode.trim()) errors.value.formCode = t('administration.governmentFormDialog.formCodeRequired')
  if (!draft.value.authorityId) errors.value.authorityId = t('administration.governmentFormDialog.authorityRequired')
  if (!draft.value.description.trim()) errors.value.description = t('administration.governmentFormDialog.descriptionRequired')
  return Object.keys(errors.value).length === 0
}

const authorityOptions = computed<SelectOption[]>(() =>
  governmentFormStore.authorities.map((authority) => ({ label: authority.name, value: authority.id })),
)

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

function isServiceTagged(serviceName: string): boolean {
  return draft.value.serviceTags.includes(serviceName)
}
function toggleServiceTag(serviceName: string): void {
  draft.value.serviceTags = isServiceTagged(serviceName)
    ? draft.value.serviceTags.filter((tag) => tag !== serviceName)
    : [...draft.value.serviceTags, serviceName]
}

const isUploadingSample = ref(false)
// Local display value so the "currently attached" filename updates
// immediately after a successful upload -- existingForm itself won't
// reflect it until governmentFormStore's own list refreshes.
const uploadedSampleFileName = ref<string | null>(null)

async function handleSampleFileSelected(event: Event): Promise<void> {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file || !existingForm.value) return
  isUploadingSample.value = true
  try {
    await governmentFormStore.uploadSampleFile(existingForm.value.id, file)
    uploadedSampleFileName.value = file.name
    toastStore.show('success', t('administration.governmentFormDialog.sampleUploadedTitle'), t('administration.governmentFormDialog.sampleUploadedDescription', { name: file.name }))
  } catch (error) {
    toastStore.show('error', t('common.uploadFailed'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isUploadingSample.value = false
    ;(event.target as HTMLInputElement).value = ''
  }
}

const isSaving = ref(false)
async function submitForm(): Promise<void> {
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

  isSaving.value = true
  try {
    if (existingForm.value) {
      await governmentFormStore.updateForm(existingForm.value.id, input)
      toastStore.show('success', t('administration.governmentFormsPanel.formUpdatedTitle'), t('administration.governmentFormsPanel.formUpdatedDescription', { title: input.title }))
    } else {
      await governmentFormStore.createForm(input)
      toastStore.show('success', t('administration.governmentFormsPanel.formAddedTitle'), t('administration.governmentFormsPanel.formAddedDescription', { title: input.title }))
    }
    goBack()
  } catch {
    toastStore.show('error', t('administration.governmentFormsPanel.unableToSaveForm'), t('common.pleaseTryAgain'))
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <BaseButton variant="ghost" size="sm" :icon="backIcon" class="self-start no-print" @click="goBack">
      {{ t('administration.governmentFormsPanel.backToForms') }}
    </BaseButton>

    <div v-if="isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="8" />
    </div>

    <EmptyState
      v-else-if="!isCreateMode && !existingForm"
      :title="t('administration.governmentFormsPanel.formNotFoundTitle')"
      :description="t('administration.governmentFormsPanel.formNotFoundDescription')"
    />

    <div v-else class="rounded-xl border border-border-light bg-bg-card p-5">
      <h1 class="mb-4 text-lg font-semibold text-text-primary">
        {{ existingForm ? t('administration.governmentFormDialog.editTitle') : t('administration.governmentFormDialog.addTitle') }}
      </h1>

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
          :hint="t('administration.governmentFormDialog.templateContentHint', { tokens: TEMPLATE_TOKEN_EXAMPLES })"
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

        <div v-if="existingForm" class="flex flex-col gap-2 rounded-lg border border-border-light p-4">
          <p class="text-sm font-medium text-text-secondary">{{ t('administration.governmentFormDialog.sampleFormTitle') }}</p>
          <p class="text-xs text-text-muted">
            {{ t('administration.governmentFormDialog.sampleFormHint') }}
          </p>
          <p v-if="uploadedSampleFileName ?? existingForm.sampleFileName" class="text-xs text-text-secondary">
            {{ t('administration.governmentFormDialog.currentlyAttached', { name: uploadedSampleFileName ?? existingForm.sampleFileName }) }}
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
            v-if="serviceCatalogStore.services.length === 0"
            :title="t('administration.governmentFormDialog.noServicesTitle')"
            :description="t('administration.governmentFormDialog.noServicesDescription')"
          />
          <div v-else class="grid grid-cols-1 gap-1.5 rounded-lg border border-border-light p-3 tablet:grid-cols-2">
            <Checkbox
              v-for="service in serviceCatalogStore.services"
              :key="service.id"
              :model-value="isServiceTagged(service.name)"
              :label="service.name"
              @update:model-value="toggleServiceTag(service.name)"
            />
          </div>
        </div>
      </div>

      <FormActionBar
        class="mt-6"
        :submit-label="t('administration.governmentFormDialog.saveForm')"
        :loading="isSaving"
        @submit="submitForm"
        @cancel="goBack"
      />
    </div>
  </div>
</template>
