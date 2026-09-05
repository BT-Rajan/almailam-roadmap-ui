<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { governmentFormService } from '@/services/governmentFormService'
import { useCompanyStore } from '@/stores/companyStore'
import { useDocumentStore } from '@/stores/documentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { GovernmentForm } from '@/types/Government'
import { extractTemplateTokens, renderGovernmentFormTemplate } from '@/utils/governmentFormHelpers'
import { formatDate } from '@/utils/dateFormatter'

const props = defineProps<{
  modelValue: boolean
  projectId: string
  // Forms this dialog can offer -- already filtered to Active forms with
  // a template by the caller (see ProjectOverviewTab.vue), so this
  // stays a dumb picker rather than re-deriving that filter itself.
  forms: GovernmentForm[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const projectStore = useProjectStore()
const companyStore = useCompanyStore()
const documentStore = useDocumentStore()
const resultDialogStore = useResultDialogStore()
const { t } = useI18n()

const project = computed(() => projectStore.projects.find((item) => item.id === props.projectId))
const client = computed(() => (project.value ? projectStore.getClientById(project.value.clientId) : undefined))

const formOptions = computed(() => props.forms.map((form) => ({ label: `${form.formCode} · ${form.title}`, value: form.id })))
const selectedFormId = ref('')
const selectedForm = computed(() => props.forms.find((form) => form.id === selectedFormId.value))
const tokens = computed(() => (selectedForm.value?.template ? extractTemplateTokens(selectedForm.value.template) : []))

const titleOverride = ref('')
const contextValues = reactive<Record<string, string>>({})
const isSaving = ref(false)
const formError = ref('')

// Pre-fills whatever real project/client/company data a token's name
// already matches (the same convention documented in
// GovernmentFormFormDialog.vue's Template Content hint) -- anything else
// (e.g. this project's own Kuwait plot fields, which have no home in the
// data model) is left blank for manual entry.
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

function humanizeToken(token: string): string {
  const spaced = token.replace(/([a-z])([A-Z])/g, '$1 $2')
  return spaced.charAt(0).toUpperCase() + spaced.slice(1)
}

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    if (companyStore.settings === undefined) companyStore.loadSettings()
    selectedFormId.value = props.forms.length === 1 ? props.forms[0].id : ''
    titleOverride.value = ''
    formError.value = ''
  },
)

watch(selectedForm, (form) => {
  for (const key of Object.keys(contextValues)) delete contextValues[key]
  if (!form?.template) return
  for (const token of extractTemplateTokens(form.template)) {
    contextValues[token] = knownDefault(token)
  }
})

const renderedPreview = computed(() =>
  selectedForm.value?.template ? renderGovernmentFormTemplate(selectedForm.value.template, contextValues) : '',
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

async function handleGenerate(): Promise<void> {
  if (!selectedForm.value) {
    formError.value = 'Please select a form'
    return
  }
  formError.value = ''
  isSaving.value = true
  try {
    const document = await governmentFormService.fillForm(selectedForm.value.id, {
      projectId: props.projectId,
      context: { ...contextValues },
      title: titleOverride.value.trim() || undefined,
    })
    documentStore.addDocument(document)
    resultDialogStore.showSuccess('Form filled and saved', `${document.title} was saved as a document on this project.`)
    closeDialog()
  } catch (error) {
    resultDialogStore.showError(
      'Failed to generate document',
      error instanceof Error ? error.message : 'Please try again.',
    )
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="t('government.fillFormDialog.title')" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <EmptyState
        v-if="forms.length === 0"
        :title="t('government.fillFormDialog.noFillableFormsTitle')"
        :description="t('government.fillFormDialog.noFillableFormsDescription')"
      />

      <template v-else>
        <SelectBox v-model="selectedFormId" :label="t('government.fillFormDialog.form')" :options="formOptions" :error="formError" required />

        <template v-if="selectedForm">
          <TextInput
            v-model="titleOverride"
            :label="t('government.fillFormDialog.documentTitle')"
            :placeholder="selectedForm.title"
            :hint="t('government.fillFormDialog.documentTitleHint')"
          />

          <div v-if="tokens.length > 0" class="flex flex-col gap-3">
            <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('government.fillFormDialog.fillInTheDetails') }}</p>
            <div class="grid grid-cols-1 gap-3 tablet:grid-cols-2">
              <TextInput
                v-for="token in tokens"
                :key="token"
                v-model="contextValues[token]"
                :label="humanizeToken(token)"
              />
            </div>
          </div>

          <div>
            <p class="mb-1.5 text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('government.fillFormDialog.preview') }}</p>
            <pre
              class="max-h-72 overflow-y-auto whitespace-pre-wrap rounded-lg border border-border-light bg-bg-card p-4 font-sans text-sm leading-relaxed text-text-primary"
              >{{ renderedPreview }}</pre
            >
          </div>
        </template>
      </template>
    </div>

    <template v-if="forms.length > 0" #footer>
      <BaseButton variant="secondary" :disabled="isSaving" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="isSaving" :disabled="!selectedForm" @click="handleGenerate">{{ t('government.fillFormDialog.generateAndSavePdf') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
