<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { FORM_CATEGORY_OPTIONS, FORM_LANGUAGE_OPTIONS } from '@/constants/governmentFormOptions'
import type { FormInput } from '@/services/governmentFormService'
import type { GovernmentAuthority, GovernmentForm, GovernmentFormCategory, GovernmentFormLanguage } from '@/types/Government'
import type { SelectOption } from '@/types/Ui'

interface Props {
  modelValue: boolean
  form?: GovernmentForm
  authorities: GovernmentAuthority[]
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

function emptyDraft(): FormInput & { requiredDocumentsText: string } {
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
  }
}

const draft = ref(emptyDraft())
const errors = ref<Record<string, string>>({})

const authorityOptions = computed<SelectOption[]>(() =>
  props.authorities.map((authority) => ({ label: authority.name, value: authority.id })),
)

watch(
  () => [props.modelValue, props.form] as const,
  ([isOpen, existingForm]) => {
    if (!isOpen) return
    draft.value = existingForm
      ? { ...existingForm, requiredDocumentsText: existingForm.requiredDocuments.join('\n') }
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
      <TextArea v-model="draft.description" label="Description" :rows="3" />
      <TextArea
        v-model="draft.requiredDocumentsText"
        label="Required Documents"
        hint="One document per line."
        :rows="4"
      />
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="saving" @click="emit('update:modelValue', false)">Cancel</BaseButton>
      <BaseButton :loading="saving" @click="handleSave">Save Form</BaseButton>
    </template>
  </BaseDialog>
</template>
