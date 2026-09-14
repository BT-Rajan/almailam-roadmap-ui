<script setup lang="ts">
import { ArrowLeft, ArrowRight } from '@lucide/vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextArea from '@/components/common/TextArea.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import { useLocale } from '@/composables/useLocale'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { SelectOption } from '@/types/Ui'
import { formMatchesProjectService } from '@/utils/governmentFormHelpers'
import { validators } from '@/utils/validators'

// Replaces NewSubmissionDialog.vue's modal -- a dedicated route
// (/government/submissions/new), same treatment as TaskCreatePage.vue/
// PaymentPlanFormPage.vue/QuotationCreatePage.vue/ContractCreatePage.vue.
// Opened two ways, both preserved from the dialog: the global Permit
// Applications list (any project pickable) and a project's own Overview
// card (?projectId=&locked=1, same convention as TaskCreatePage's own
// ProjectTasksTab origin -- the project field is fixed, not just prefilled).

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isRtl } = useLocale()
const submissionStore = useGovernmentSubmissionStore()
const resultDialogStore = useResultDialogStore()

const backIcon = computed(() => (isRtl.value ? ArrowRight : ArrowLeft))

const queryProjectId = computed(() => {
  const value = route.query.projectId
  return typeof value === 'string' ? value : undefined
})
const isProjectLocked = computed(() => route.query.locked === '1')

const isLoading = ref(true)

async function loadData(): Promise<void> {
  isLoading.value = true
  if (submissionStore.authorities.length === 0 || submissionStore.forms.length === 0) {
    await submissionStore.loadSubmissions()
  }
  isLoading.value = false
}
onMounted(loadData)

function goBack(): void {
  if (isProjectLocked.value && queryProjectId.value) {
    // Opening a project always lands on Workflow Progress Stage 1
    // (Requirement/Scope) -- see SubmissionWorkspacePage.vue's own
    // goBack for why this doesn't carry a ?tab= query.
    router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: queryProjectId.value } })
    return
  }
  router.push({ name: ROUTE_NAMES.GOVERNMENT_SUBMISSIONS })
}

function emptyForm() {
  return {
    projectId: '',
    authorityId: '',
    formId: '',
    selectedPermitId: '',
    expectedDecisionDate: '',
    notes: '',
  }
}

const form = reactive(emptyForm())
const { errors, setRules, validateAll } = useFormValidation()

setRules({
  projectId: [validators.required('Please select a project')],
  authorityId: [validators.required('Please select an authority')],
  formId: [validators.required('Please select a form')],
})

const availableProjects = computed(() => {
  if (isProjectLocked.value) {
    return submissionStore.projects.filter((project) => project.id === queryProjectId.value)
  }
  return submissionStore.projects
})

const projectOptions = computed<SelectOption[]>(() =>
  availableProjects.value.map((project) => ({ label: project.projectName, value: project.id })),
)

const authorityOptions = computed<SelectOption[]>(() =>
  submissionStore.authorities.map((authority) => ({ label: authority.name, value: authority.id })),
)

const selectedProject = computed(() => submissionStore.projects.find((project) => project.id === form.projectId))

// A form always belongs to exactly one authority -- narrowing the list
// this way means the person can never end up picking a mismatched pair.
const formsForAuthority = computed(() => submissionStore.forms.filter((formItem) => formItem.authorityId === form.authorityId))

// Further narrowed to forms actually relevant to this project's service
// (Administration > Service Document Map), same rule the Overview tab's
// Required Documents card already uses.
const scopedForms = computed(() =>
  selectedProject.value
    ? formsForAuthority.value.filter((formItem) => formMatchesProjectService(formItem, selectedProject.value!.service))
    : formsForAuthority.value,
)

const formOptions = computed<SelectOption[]>(() =>
  scopedForms.value.map((formItem) => ({ label: `${formItem.formCode} — ${formItem.title}`, value: formItem.id })),
)

const scopeMismatchHint = computed(() =>
  form.authorityId && formsForAuthority.value.length > 0 && scopedForms.value.length === 0
    ? t('government.newSubmissionDialog.scopeMismatchHint')
    : undefined,
)

const selectedForm = computed(() => submissionStore.forms.find((formItem) => formItem.id === form.formId))

// The type of approval this application is fulfilling, if the project
// already planned it at setup (New Project Wizard's Permits step) --
// optional, an application can still be filed ad hoc with no such link.
const permitOptions = computed<SelectOption[]>(
  () =>
    selectedProject.value?.selectedPermits?.map((permit) => ({
      label: `${permit.permitName} (${permit.status})`,
      value: permit.id,
    })) ?? [],
)

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
  () => form.projectId,
  () => {
    // Planned permits are per-project -- clear the linked permit rather
    // than silently keep another project's selection.
    form.selectedPermitId = ''
  },
)

// Seeds the project field once loading finishes (prefilled/locked from
// ?projectId=, or the first available project) -- mirrors the dialog's
// own reset-on-open, just gated on data having actually arrived.
const isFormSeeded = ref(false)
watch(
  () => [isLoading.value, availableProjects.value] as const,
  ([loading, projects]) => {
    if (loading || isFormSeeded.value) return
    form.projectId = queryProjectId.value ?? projects[0]?.id ?? ''
    isFormSeeded.value = true
    revalidate()
  },
  { immediate: true },
)

function revalidate(): void {
  validateAll(form)
}
watch(form, revalidate, { deep: true })

const isSubmitting = ref(false)

async function handleSubmit(): Promise<void> {
  if (!validateAll(form)) return
  isSubmitting.value = true
  try {
    const submission = await submissionStore.createSubmission({
      projectId: form.projectId,
      authorityId: form.authorityId,
      formId: form.formId,
      selectedPermitId: form.selectedPermitId || undefined,
      expectedDecisionDate: form.expectedDecisionDate || undefined,
      notes: form.notes.trim() || undefined,
    })
    resultDialogStore.showSuccess(
      t('government.submissionsPage.submissionCreatedTitle'),
      t('common.createdSuccessfully', { no: submission.submissionNo }),
    )
    // Lands straight on the new application's own workspace, same as
    // TaskCreatePage.vue does for a newly created task -- carrying
    // ?projectId= when opened from a project so its own "Back to
    // Project" keeps working immediately.
    router.push({
      name: ROUTE_NAMES.SUBMISSION_WORKSPACE,
      params: { submissionNo: submission.submissionNo },
      query: isProjectLocked.value && queryProjectId.value ? { projectId: queryProjectId.value } : undefined,
    })
  } catch (error) {
    resultDialogStore.showError(
      t('government.submissionsPage.failedToCreateSubmission'),
      error instanceof Error ? error.message : t('common.pleaseTryAgain'),
    )
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <BaseButton variant="ghost" size="sm" :icon="backIcon" class="self-start no-print" @click="goBack">
      {{ isProjectLocked ? t('government.workspacePage.backToProject') : t('government.workspacePage.backToSubmissions') }}
    </BaseButton>

    <div v-if="isLoading" class="max-w-2xl rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="8" />
    </div>

    <div v-else class="max-w-2xl rounded-xl border border-border-light bg-bg-card p-5">
      <h1 class="mb-4 text-lg font-semibold text-text-primary">{{ t('government.newSubmissionDialog.title') }}</h1>

      <div class="flex flex-col gap-5">
        <SelectBox
          v-model="form.projectId"
          :label="t('government.newSubmissionDialog.project')"
          required
          :disabled="isProjectLocked"
          :options="projectOptions"
          :error="errors.projectId"
        />

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

        <SelectBox
          v-if="permitOptions.length > 0"
          v-model="form.selectedPermitId"
          :label="t('government.newSubmissionDialog.linkedPermit')"
          :placeholder="t('government.newSubmissionDialog.linkedPermitPlaceholder')"
          :options="permitOptions"
        />

        <DatePicker v-model="form.expectedDecisionDate" :label="t('government.newSubmissionDialog.expectedDecisionDate')" />
        <TextArea v-model="form.notes" :label="t('common.notes')" :placeholder="t('government.newSubmissionDialog.notesPlaceholder')" :rows="2" />

        <div v-if="selectedForm && selectedForm.requiredDocuments.length > 0" class="rounded-lg bg-bg-secondary p-4 text-sm">
          <p class="mb-2 font-medium text-text-secondary">{{ t('government.newSubmissionDialog.thisFormRequires') }}</p>
          <ul class="flex flex-col gap-1 text-text-secondary">
            <li v-for="documentName in selectedForm.requiredDocuments" :key="documentName">• {{ documentName }}</li>
          </ul>
        </div>
      </div>

      <div class="mt-6 flex justify-end gap-3">
        <BaseButton variant="secondary" :disabled="isSubmitting" @click="goBack">{{ t('common.cancel') }}</BaseButton>
        <BaseButton :loading="isSubmitting" @click="handleSubmit">{{ t('government.newSubmissionDialog.createSubmission') }}</BaseButton>
      </div>
    </div>
  </div>
</template>
