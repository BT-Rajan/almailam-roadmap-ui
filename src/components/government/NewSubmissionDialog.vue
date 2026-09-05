<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import type { SubmissionCreateInput } from '@/services/governmentSubmissionService'
import type { GovernmentAuthority, GovernmentForm } from '@/types/Government'
import type { Project } from '@/types/Project'
import type { SelectOption } from '@/types/Ui'
import { formMatchesProjectService } from '@/utils/governmentFormHelpers'
import { validators } from '@/utils/validators'

const props = defineProps<{
  modelValue: boolean
  projects: Project[]
  authorities: GovernmentAuthority[]
  forms: GovernmentForm[]
  defaultProjectId?: string
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: SubmissionCreateInput]
}>()

function emptyForm() {
  return {
    projectId: '',
    authorityId: '',
    formId: '',
    expectedDecisionDate: '',
    notes: '',
  }
}

const { t } = useI18n()

const form = reactive(emptyForm())
const { errors, setRules, validateAll } = useFormValidation()

setRules({
  projectId: [validators.required('Please select a project')],
  authorityId: [validators.required('Please select an authority')],
  formId: [validators.required('Please select a form')],
})

const projectOptions = computed<SelectOption[]>(() =>
  props.projects.map((project) => ({ label: project.projectName, value: project.id })),
)

const authorityOptions = computed<SelectOption[]>(() =>
  props.authorities.map((authority) => ({ label: authority.name, value: authority.id })),
)

const selectedProject = computed(() => props.projects.find((project) => project.id === form.projectId))

// A form always belongs to exactly one authority -- narrowing the list
// this way means the person can never end up picking a mismatched pair
// (the backend would reject it anyway, but there's no reason to let
// them get that far).
const formsForAuthority = computed(() => props.forms.filter((formItem) => formItem.authorityId === form.authorityId))

// Further narrowed to forms actually relevant to this project's service
// (Administration > Service Document Map), same rule the Overview tab's
// Required Documents card already uses -- keeps "which form applies
// here" answered one consistent way everywhere it's asked.
const scopedForms = computed(() =>
  selectedProject.value
    ? formsForAuthority.value.filter((formItem) => formMatchesProjectService(formItem, selectedProject.value!.service))
    : formsForAuthority.value,
)

const formOptions = computed<SelectOption[]>(() =>
  scopedForms.value.map((formItem) => ({ label: `${formItem.formCode} — ${formItem.title}`, value: formItem.id })),
)

// Distinguishes "this authority has no forms at all" from "none of this
// authority's forms are mapped to this project's service" -- the second
// is fixable from Administration > Service Document Map, worth saying
// so explicitly rather than just showing an empty dropdown either way.
const scopeMismatchHint = computed(() =>
  form.authorityId && formsForAuthority.value.length > 0 && scopedForms.value.length === 0
    ? t('government.newSubmissionDialog.scopeMismatchHint')
    : undefined,
)

const selectedForm = computed(() => props.forms.find((formItem) => formItem.id === form.formId))

watch(
  () => [form.authorityId, form.projectId],
  () => {
    // Changing the authority or project can invalidate whatever form was
    // selected under the old pair -- clear it rather than silently keep
    // an orphaned selection that no longer matches any visible option.
    form.formId = ''
  },
)

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    Object.assign(form, emptyForm())
    form.projectId = props.defaultProjectId ?? props.projects[0]?.id ?? ''
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  if (!validateAll(form)) return
  emit('confirm', {
    projectId: form.projectId,
    authorityId: form.authorityId,
    formId: form.formId,
    expectedDecisionDate: form.expectedDecisionDate || undefined,
    notes: form.notes.trim() || undefined,
  })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="t('government.newSubmissionDialog.title')" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-5">
      <SelectBox v-model="form.projectId" :label="t('government.newSubmissionDialog.project')" required :options="projectOptions" :error="errors.projectId" />

      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <SelectBox v-model="form.authorityId" :label="t('government.newSubmissionDialog.authority')" required :options="authorityOptions" :error="errors.authorityId" />
        <SelectBox
          v-model="form.formId"
          :label="t('government.newSubmissionDialog.form')"
          required
          :disabled="!form.authorityId"
          :options="formOptions"
          :error="errors.formId"
          :hint="!form.authorityId ? t('government.newSubmissionDialog.selectAuthorityFirstHint') : scopeMismatchHint"
        />
      </div>

      <DatePicker v-model="form.expectedDecisionDate" :label="t('government.newSubmissionDialog.expectedDecisionDate')" />
      <TextArea v-model="form.notes" :label="t('common.notes')" :placeholder="t('government.newSubmissionDialog.notesPlaceholder')" :rows="2" />

      <div v-if="selectedForm && selectedForm.requiredDocuments.length > 0" class="rounded-lg bg-bg-secondary p-4 text-sm">
        <p class="mb-2 font-medium text-text-secondary">{{ t('government.newSubmissionDialog.thisFormRequires') }}</p>
        <ul class="flex flex-col gap-1 text-text-secondary">
          <li v-for="documentName in selectedForm.requiredDocuments" :key="documentName">• {{ documentName }}</li>
        </ul>
      </div>
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">{{ t('government.newSubmissionDialog.createSubmission') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
