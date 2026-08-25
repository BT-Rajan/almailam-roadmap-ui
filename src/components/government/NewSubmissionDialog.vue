<script setup lang="ts">
import { computed, reactive, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import { GOVERNMENT_SUBMISSION_STAGE_OPTIONS } from '@/constants/processStages'
import type { SubmissionCreateInput } from '@/services/governmentSubmissionService'
import type { GovernmentAuthority, GovernmentForm } from '@/types/Government'
import type { Project } from '@/types/Project'
import type { SelectOption } from '@/types/Ui'
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
    stageKey: '',
  }
}

const stageKeyOptions: SelectOption[] = GOVERNMENT_SUBMISSION_STAGE_OPTIONS.map((stage) => ({
  label: stage.label,
  value: stage.key,
}))

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

// A form always belongs to exactly one authority -- narrowing the list
// this way means the person can never end up picking a mismatched pair
// (the backend would reject it anyway, but there's no reason to let
// them get that far).
const formOptions = computed<SelectOption[]>(() =>
  props.forms
    .filter((formItem) => formItem.authorityId === form.authorityId)
    .map((formItem) => ({ label: `${formItem.formCode} — ${formItem.title}`, value: formItem.id })),
)

const selectedForm = computed(() => props.forms.find((formItem) => formItem.id === form.formId))

watch(
  () => form.authorityId,
  () => {
    // Changing the authority invalidates whatever form was selected
    // under the old one -- clear it rather than silently keep an
    // orphaned selection that no longer matches any visible option.
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
    stageKey: form.stageKey || undefined,
  })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="New Government Submission" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-5">
      <SelectBox v-model="form.projectId" label="Project" required :options="projectOptions" :error="errors.projectId" />

      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <SelectBox v-model="form.authorityId" label="Authority" required :options="authorityOptions" :error="errors.authorityId" />
        <SelectBox
          v-model="form.formId"
          label="Form"
          required
          :disabled="!form.authorityId"
          :options="formOptions"
          :error="errors.formId"
          :hint="!form.authorityId ? 'Select an authority first' : undefined"
        />
      </div>

      <DatePicker v-model="form.expectedDecisionDate" label="Expected Decision Date (optional)" />
      <SelectBox
        v-model="form.stageKey"
        label="Approval Gate (optional)"
        placeholder="Not tied to a project approval gate"
        :options="stageKeyOptions"
        hint="Once this submission is Approved, the matching gate on the project's Process tab closes automatically."
      />
      <TextArea v-model="form.notes" label="Notes" placeholder="Optional notes for this submission" :rows="2" />

      <div v-if="selectedForm && selectedForm.requiredDocuments.length > 0" class="rounded-lg bg-bg-secondary p-4 text-sm">
        <p class="mb-2 font-medium text-text-secondary">This form requires:</p>
        <ul class="flex flex-col gap-1 text-text-secondary">
          <li v-for="documentName in selectedForm.requiredDocuments" :key="documentName">• {{ documentName }}</li>
        </ul>
      </div>
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">Create Submission</BaseButton>
    </template>
  </BaseDialog>
</template>
