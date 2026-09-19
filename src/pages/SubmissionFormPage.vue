<script setup lang="ts">
import { ArrowLeft, ArrowRight } from '@lucide/vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextArea from '@/components/common/TextArea.vue'
import ProjectStageStepper from '@/components/project/ProjectStageStepper.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import { useLocale } from '@/composables/useLocale'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { useProjectStore } from '@/stores/projectStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { SubmissionUpdateInput } from '@/services/governmentSubmissionService'
import type { SelectOption } from '@/types/Ui'
import { formMatchesProjectService } from '@/utils/governmentFormHelpers'
import { validators } from '@/utils/validators'

// New Permit Application and Edit Permit Application -- one page, like
// PaymentPlanFormPage.vue: it's an edit whenever the route carries a
// :submissionNo (SUBMISSION_EDIT / PROJECT_SUBMISSION_EDIT), otherwise a
// create. Replaces NewSubmissionDialog.vue's modal with a dedicated
// route, same treatment as TaskCreatePage.vue/QuotationCreatePage.vue/
// ContractCreatePage.vue. Opened two ways, both preserved from the dialog:
//  - the global Permit Applications list (/government/submissions/new,
//    any project pickable);
//  - a project's own Approvals & Permits card
//    (/projects/:projectId/permit-applications/new) -- the project field
//    is fixed, not just prefilled, and the project stepper and project
//    breadcrumbs stay so staff never leave the project. The older
//    ?projectId=&locked=1 query form of the global route still behaves
//    the same way.
// Editing always keeps the project fixed; the authority and form can
// only change while the application is still in Prepare with nothing
// uploaded (the API enforces the same rule), and a closed application
// can't be edited at all.

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isRtl } = useLocale()
const submissionStore = useGovernmentSubmissionStore()
const projectStore = useProjectStore()
const resultDialogStore = useResultDialogStore()

const backIcon = computed(() => (isRtl.value ? ArrowRight : ArrowLeft))

// The project this page was opened from, if any -- the route param on
// the project-scoped route, else the ?projectId= query of the global one.
const queryProjectId = computed(() => {
  const param = route.params.projectId
  if (typeof param === 'string') return param
  const value = route.query.projectId
  return typeof value === 'string' ? value : undefined
})
const isProjectLocked = computed(() => typeof route.params.projectId === 'string' || route.query.locked === '1')

// Edit mode: which application is being edited (see the header comment).
const editSubmissionNo = computed(() => (typeof route.params.submissionNo === 'string' ? route.params.submissionNo : undefined))
const isEditMode = computed(() => editSubmissionNo.value !== undefined)
const editingSubmission = computed(() => (editSubmissionNo.value ? submissionStore.getSubmissionByNo(editSubmissionNo.value) : undefined))
const isClosed = computed(() => editingSubmission.value?.stage === 'Close')

// In edit mode the project is never changeable, wherever the page was
// opened from.
const isProjectFieldFixed = computed(() => isProjectLocked.value || isEditMode.value)

// Same rule as submission_service._change_authority_and_form: nothing
// has been done against the current form yet.
const canChangeAuthorityAndForm = computed(() => {
  const submission = editingSubmission.value
  if (!submission) return !isEditMode.value
  return submission.stage === 'Prepare' && submission.documents.every((document) => document.status === 'Pending')
})

// The full project (with the workflow flags/selections the stepper
// needs) -- only looked up when opened from a project.
const originProject = computed(() =>
  isProjectLocked.value && queryProjectId.value ? projectStore.getProjectById(queryProjectId.value) : undefined,
)

const isLoading = ref(true)

async function loadData(): Promise<void> {
  isLoading.value = true
  if (isProjectLocked.value && projectStore.projects.length === 0) await projectStore.loadProjects()
  if (isEditMode.value && editSubmissionNo.value) {
    await submissionStore.loadSubmissionByNo(editSubmissionNo.value)
  } else if (submissionStore.authorities.length === 0 || submissionStore.forms.length === 0) {
    await submissionStore.loadSubmissions()
  }
  isLoading.value = false
}
onMounted(loadData)

// Back to the application being edited (in its project when this was
// opened from one), or -- when creating -- to wherever it was started.
function goBack(): void {
  if (isEditMode.value && editSubmissionNo.value) {
    if (typeof route.params.projectId === 'string') {
      router.push({
        name: ROUTE_NAMES.PROJECT_SUBMISSION_WORKSPACE,
        params: { projectId: route.params.projectId, submissionNo: editSubmissionNo.value },
      })
      return
    }
    router.push({ name: ROUTE_NAMES.SUBMISSION_WORKSPACE, params: { submissionNo: editSubmissionNo.value } })
    return
  }
  if (isProjectLocked.value && queryProjectId.value) {
    // Back to the Approvals & Permits card this was opened from.
    router.push({
      name: ROUTE_NAMES.PROJECT_WORKSPACE,
      params: { projectId: queryProjectId.value },
      query: { tab: 'government', view: 'overview' },
    })
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
  if (isEditMode.value && editingSubmission.value) {
    return submissionStore.projects.filter((project) => project.id === editingSubmission.value!.projectId)
  }
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

const formOptions = computed<SelectOption[]>(() => {
  const options = scopedForms.value.map((formItem) => ({ label: `${formItem.formCode} — ${formItem.title}`, value: formItem.id }))
  // An application's own form always stays selectable when editing, even
  // if the Service Document Map no longer maps it to this project.
  const current = editingSubmission.value ? submissionStore.forms.find((formItem) => formItem.id === editingSubmission.value!.formId) : undefined
  if (current && current.authorityId === form.authorityId && !options.some((option) => option.value === current.id)) {
    options.unshift({ label: `${current.formCode} — ${current.title}`, value: current.id })
  }
  return options
})

const scopeMismatchHint = computed(() =>
  form.authorityId && formsForAuthority.value.length > 0 && scopedForms.value.length === 0
    ? t('government.newSubmissionDialog.scopeMismatchHint')
    : undefined,
)

const formHint = computed(() => {
  if (isEditMode.value && !canChangeAuthorityAndForm.value) return t('government.newSubmissionDialog.authorityFormLockedHint')
  if (!form.authorityId) return t('government.newSubmissionDialog.selectAuthorityFirstHint')
  return scopeMismatchHint.value
})

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
    // (Only when it really no longer matches: seeding an edit sets the
    // authority and form together and must keep both.)
    if (form.formId && !formOptions.value.some((option) => option.value === form.formId)) form.formId = ''
  },
)

watch(
  () => form.projectId,
  () => {
    // Planned permits are per-project -- clear the linked permit rather
    // than silently keep another project's selection.
    if (form.selectedPermitId && !permitOptions.value.some((option) => option.value === form.selectedPermitId)) {
      form.selectedPermitId = ''
    }
  },
)

// Seeds the project field once loading finishes (prefilled/locked from
// ?projectId=, or the first available project) -- mirrors the dialog's
// own reset-on-open, just gated on data having actually arrived.
const isFormSeeded = ref(false)
watch(
  () => [isLoading.value, availableProjects.value, editingSubmission.value] as const,
  ([loading, projects]) => {
    if (loading || isFormSeeded.value) return
    const existing = editingSubmission.value
    if (isEditMode.value) {
      // Nothing to seed until the application itself has loaded (or it
      // doesn't exist / is closed, which the template reports).
      if (!existing || existing.stage === 'Close') return
      form.projectId = existing.projectId
      form.authorityId = existing.authorityId
      form.formId = existing.formId
      form.selectedPermitId = existing.selectedPermitId ?? ''
      form.expectedDecisionDate = existing.expectedDecisionDate ?? ''
      form.notes = existing.notes ?? ''
    } else {
      form.projectId = queryProjectId.value ?? projects[0]?.id ?? ''
    }
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

async function handleUpdate(submissionNo: string): Promise<void> {
  const input: SubmissionUpdateInput = {
    expectedDecisionDate: form.expectedDecisionDate || null,
    notes: form.notes.trim() || null,
    selectedPermitId: form.selectedPermitId || null,
  }
  // Authority/form are only ever sent when the API would accept a change.
  if (canChangeAuthorityAndForm.value) {
    input.authorityId = form.authorityId
    input.formId = form.formId
  }
  isSubmitting.value = true
  try {
    await submissionStore.updateSubmission(submissionNo, input)
    resultDialogStore.showSuccess(
      t('government.submissionsPage.submissionUpdatedTitle'),
      t('government.submissionsPage.submissionUpdatedDescription', { no: submissionNo }),
    )
    goBack()
  } catch (error) {
    resultDialogStore.showError(
      t('government.submissionsPage.failedToUpdateSubmission'),
      error instanceof Error ? error.message : t('common.pleaseTryAgain'),
    )
  } finally {
    isSubmitting.value = false
  }
}

async function handleSubmit(): Promise<void> {
  if (!validateAll(form)) return
  if (isEditMode.value && editSubmissionNo.value) {
    await handleUpdate(editSubmissionNo.value)
    return
  }
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
    // TaskCreatePage.vue does for a newly created task -- the
    // project-scoped one when opened from a project, so the stepper and
    // "Back to Project" carry straight over.
    if (isProjectLocked.value && queryProjectId.value) {
      router.push({
        name: ROUTE_NAMES.PROJECT_SUBMISSION_WORKSPACE,
        params: { projectId: queryProjectId.value, submissionNo: submission.submissionNo },
      })
      return
    }
    router.push({ name: ROUTE_NAMES.SUBMISSION_WORKSPACE, params: { submissionNo: submission.submissionNo } })
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
    <ProjectStageStepper v-if="originProject" :project="originProject" />
    <BaseButton v-else variant="ghost" size="sm" :icon="backIcon" class="self-start no-print" @click="goBack">
      {{
        isEditMode
          ? t('government.newSubmissionDialog.backToApplication')
          : isProjectLocked
            ? t('government.workspacePage.backToProject')
            : t('government.workspacePage.backToSubmissions')
      }}
    </BaseButton>

    <div v-if="isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="8" />
    </div>

    <EmptyState
      v-else-if="isEditMode && !editingSubmission"
      :title="t('government.workspacePage.submissionNotFound')"
      :description="t('government.workspacePage.submissionNotFoundDescription')"
    />

    <EmptyState
      v-else-if="isEditMode && isClosed"
      :title="t('government.newSubmissionDialog.closedTitle')"
      :description="t('government.newSubmissionDialog.closedDescription')"
    />

    <div v-else class="rounded-xl border border-border-light bg-bg-card p-5">
      <h1 class="mb-4 text-lg font-semibold text-text-primary">
        {{ isEditMode ? t('government.newSubmissionDialog.editTitle') : t('government.newSubmissionDialog.title') }}
      </h1>

      <div class="flex flex-col gap-5">
        <SelectBox
          v-model="form.projectId"
          :label="t('government.newSubmissionDialog.project')"
          required
          :disabled="isProjectFieldFixed"
          :options="projectOptions"
          :error="errors.projectId"
        />

        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <SelectBox
            v-model="form.authorityId"
            :label="t('government.newSubmissionDialog.authority')"
            required
            :disabled="!canChangeAuthorityAndForm"
            :options="authorityOptions"
            :error="errors.authorityId"
          />
          <SelectBox
            v-model="form.formId"
            :label="t('government.newSubmissionDialog.form')"
            required
            :disabled="!form.authorityId || !canChangeAuthorityAndForm"
            :options="formOptions"
            :error="errors.formId"
            :hint="formHint"
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
        <BaseButton :loading="isSubmitting" @click="handleSubmit">{{ isEditMode ? t('government.newSubmissionDialog.saveChanges') : t('government.newSubmissionDialog.createSubmission') }}</BaseButton>
      </div>
    </div>
  </div>
</template>
