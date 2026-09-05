<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import RadioGroup from '@/components/common/RadioGroup.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useCompanyStore } from '@/stores/companyStore'
import { useProjectFormStore } from '@/stores/projectFormStore'
import { useProjectStore } from '@/stores/projectStore'
import type { GovernmentForm, GovernmentFormField, ProjectFormEntry } from '@/types/Government'
import type { SelectOption } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'
import { extractTemplateTokens, renderGovernmentFormTemplate } from '@/utils/governmentFormHelpers'

const props = defineProps<{
  modelValue: boolean
  projectId: string
  form?: GovernmentForm
  // Set when re-filling an already-saved entry -- prefills from its
  // saved field_values instead of the "known" defaults below, and Save
  // updates that same entry instead of creating a new one.
  entry?: ProjectFormEntry
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const projectStore = useProjectStore()
const companyStore = useCompanyStore()
const projectFormStore = useProjectFormStore()
const { t } = useI18n()

const project = computed(() => projectStore.projects.find((item) => item.id === props.projectId))
const client = computed(() => (project.value ? projectStore.getClientById(project.value.clientId) : undefined))

// Every {{token}} in the template gets a control -- one declared in
// form.fields (dropdown/radio, per the admin's own definition) if
// there is one for it, otherwise a plain text box.
const templateTokens = computed(() => (props.form?.template ? extractTemplateTokens(props.form.template) : []))

function fieldFor(token: string): GovernmentFormField | undefined {
  return props.form?.fields.find((f) => f.token === token)
}

function fieldOptions(field: GovernmentFormField): SelectOption[] {
  return field.options.map((option) => ({ label: option, value: option }))
}

const contextValues = reactive<Record<string, string>>({})
const isSaving = ref(false)
const formError = ref('')

function knownDefault(token: string): string {
  switch (token) {
    case 'date':
      return formatDate(new Date().toISOString())
    case 'companyName':
      return companyStore.settings?.companyName ?? ''
    case 'clientName':
      return client.value?.companyName ?? ''
    case 'projectName':
      return project.value?.projectName ?? ''
    case 'engineerName':
      return project.value?.engineer ?? ''
    default:
      return ''
  }
}

watch(
  () => [props.modelValue, props.form, props.entry] as const,
  ([isOpen, form, entry]) => {
    if (!isOpen) return
    if (companyStore.settings === undefined) companyStore.loadSettings()
    for (const key of Object.keys(contextValues)) delete contextValues[key]
    if (!form?.template) return
    for (const token of extractTemplateTokens(form.template)) {
      contextValues[token] = entry?.fieldValues[token] ?? knownDefault(token)
    }
    formError.value = ''
  },
  { immediate: true },
)

const renderedPreview = computed(() =>
  props.form?.template ? renderGovernmentFormTemplate(props.form.template, contextValues) : '',
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

async function handleSave(): Promise<void> {
  if (!props.form) return
  formError.value = ''
  isSaving.value = true
  try {
    const saved = props.entry
      ? await projectFormStore.updateEntry(props.projectId, props.entry.id, { ...contextValues })
      : await projectFormStore.createEntry(props.projectId, props.form.id, { ...contextValues })
    if (!saved) {
      formError.value = projectFormStore.mutationError ?? 'Failed to save the form.'
      return
    }
    closeDialog()
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="
      form
        ? entry
          ? t('government.projectFormEntryDialog.editTitle', { name: form.title })
          : t('government.projectFormEntryDialog.fillTitle', { name: form.title })
        : t('government.projectFormEntryDialog.defaultTitle')
    "
    size="lg"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-if="form" class="flex flex-col gap-4">
      <div v-if="templateTokens.length > 0" class="flex flex-col gap-3">
        <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('government.projectFormEntryDialog.fillInTheDetails') }}</p>
        <div class="grid grid-cols-1 gap-3 tablet:grid-cols-2">
          <template v-for="token in templateTokens" :key="token">
            <SelectBox
              v-if="fieldFor(token)?.type === 'select'"
              v-model="contextValues[token]"
              :label="fieldFor(token)!.label"
              :options="fieldOptions(fieldFor(token)!)"
            />
            <div v-else-if="fieldFor(token)?.type === 'radio'" class="tablet:col-span-2">
              <RadioGroup v-model="contextValues[token]" :label="fieldFor(token)!.label" :options="fieldOptions(fieldFor(token)!)" />
            </div>
            <TextInput v-else v-model="contextValues[token]" :label="fieldFor(token)?.label ?? token" />
          </template>
        </div>
      </div>

      <div>
        <p class="mb-1.5 text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('government.projectFormEntryDialog.preview') }}</p>
        <pre
          class="max-h-72 overflow-y-auto whitespace-pre-wrap rounded-lg border border-border-light bg-bg-card p-4 font-sans text-sm leading-relaxed text-text-primary"
          >{{ renderedPreview }}</pre
        >
      </div>

      <p v-if="formError" class="text-xs text-danger-600">{{ formError }}</p>
    </div>

    <template v-if="form" #footer>
      <BaseButton variant="secondary" :disabled="isSaving" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="isSaving" @click="handleSave">{{ t('government.projectFormEntryDialog.saveAndGeneratePdf') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
