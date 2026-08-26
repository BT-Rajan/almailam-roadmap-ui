<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { FORM_CATEGORY_OPTIONS, FORM_LANGUAGE_OPTIONS } from '@/constants/governmentFormOptions'
import type { FormInput } from '@/services/governmentFormService'
import type { GovernmentAuthority, GovernmentForm, GovernmentFormCategory, GovernmentFormLanguage } from '@/types/Government'
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
  }

  emit('save', input)
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="form ? 'Edit Government Form' : 'Add Government Form'"
    size="lg"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="flex flex-col gap-4">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <TextInput v-model="draft.title" label="Form Title" :error="errors.title" required />
        <TextInput v-model="draft.formCode" label="Form Code" placeholder="e.g. MUN-BP-01" :error="errors.formCode" required />
      </div>

      <SelectBox v-model="draft.authorityId" label="Authority" :options="authorityOptions" :error="errors.authorityId" required />

      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
        <SelectBox v-model="draft.category" label="Category" :options="FORM_CATEGORY_OPTIONS" />
        <SelectBox v-model="draft.language" label="Language" :options="FORM_LANGUAGE_OPTIONS" />
        <TextInput v-model="draft.version" label="Version" placeholder="v1.0" />
      </div>

      <DatePicker v-model="draft.lastUpdated" label="Last Updated" />
      <TextArea v-model="draft.description" label="Description" :rows="3" :error="errors.description" required />
      <TextArea
        v-model="draft.requiredDocumentsText"
        label="Required Documents"
        hint="One document per line."
        :rows="4"
      />

      <TextArea
        v-model="draft.template"
        label="Template Content"
        hint="Written with {{token}} merge fields, e.g. {{clientName}}, {{projectName}}, {{projectAddress}}, {{companyName}}, {{engineerName}}, {{date}}. Used to preview and print this form filled in."
        :rows="8"
      />

      <div>
        <p class="mb-1.5 text-sm font-medium text-text-secondary">Tagged Services</p>
        <p class="mb-2 text-xs text-text-muted">
          This form is suggested under a project's Documents &gt; Government section when the project's service
          matches one of the tags below.
        </p>
        <EmptyState
          v-if="services.length === 0"
          title="No services in the catalog yet"
          description="Add services under Administration > Service Catalog to tag this form."
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
      <BaseButton variant="secondary" :disabled="saving" @click="emit('update:modelValue', false)">Cancel</BaseButton>
      <BaseButton :loading="saving" @click="handleSave">Save Form</BaseButton>
    </template>
  </BaseDialog>
</template>
