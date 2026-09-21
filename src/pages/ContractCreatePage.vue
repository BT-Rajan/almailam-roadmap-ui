<script setup lang="ts">
import { FileSignature, Plus, Trash2 } from '@lucide/vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import Divider from '@/components/common/Divider.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import RichTextEditor from '@/components/common/RichTextEditor.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextInput from '@/components/common/TextInput.vue'
import WorkflowProgress from '@/components/project/WorkflowProgress.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useContractStore } from '@/stores/contractStore'
import { usePaymentStore } from '@/stores/paymentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { ContractClauseInput } from '@/services/contractService'
import type { Project, ProjectWorkspaceTabKey } from '@/types/Project'
import type { Quotation } from '@/types/Quotation'
import { getClientFormalName } from '@/utils/clientHelpers'
import { getDesignPermitPeriod, getSupervisionPeriod, isRichTextBlank, scopeSummaryToHtml } from '@/utils/contractHelpers'
import { formatDate, todayIso } from '@/utils/dateFormatter'
import { sanitizeHtml } from '@/utils/sanitizeHtml'
import { validators } from '@/utils/validators'

// Dedicated route (/projects/:projectId/contract/new). Editing an
// existing contract happens inline on the Contract tab
// (ContractPreview.vue).
//
// Laid out as the contract document itself (same shape as
// ContractPreview.vue) with only the fields staff actually decide --
// Expiry Date and Clauses -- editable in place.
// Everything else (client, project, Design & Permit / Supervision
// dates, scope, value) is filled in automatically and locked.

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const projectStore = useProjectStore()
const quotationStore = useQuotationStore()
const contractStore = useContractStore()
const paymentStore = usePaymentStore()
const resultDialogStore = useResultDialogStore()

const projectId = computed(() => route.params.projectId as string)
// Set when navigated here via "Advance to Contract" on the Payment Plan
// tab -- pins which quotation this contract is generated from. Omitted,
// eligibleQuotation below falls back to the same
// selected-else-latest rule ProjectContractTab.vue always used.
const queryQuotationId = computed(() => {
  const value = route.query.quotationId
  return typeof value === 'string' ? value : undefined
})

const isLoading = ref(true)

async function loadData(): Promise<void> {
  isLoading.value = true
  if (projectStore.projects.length === 0) await projectStore.loadProjects()
  await Promise.all([
    quotationStore.loadQuotationsForProject(projectId.value),
    contractStore.loadContractsForProject(projectId.value),
    // The approved payment plan(s) come first in the workflow and the
    // contract has to fit them -- see lastInstallmentDate below.
    paymentStore.loadForProject(projectId.value),
  ])
  isLoading.value = false
}
onMounted(loadData)
watch(projectId, loadData)

const project = computed(() => projectStore.getProjectById(projectId.value))
const client = computed(() => (project.value ? projectStore.getClientById(project.value.clientId) : undefined))

// A contract must come from a specific quotation that's Approved and
// Final (see contract_service.create_contract).
const eligibleQuotation = computed<Quotation | undefined>(() => {
  const candidate = queryQuotationId.value
    ? quotationStore.quotations.find((quotation) => quotation.id === queryQuotationId.value)
    : (quotationStore.selectedQuotation ?? quotationStore.latestQuotation)
  return candidate && candidate.status === 'Approved' && candidate.finalizedAt ? candidate : undefined
})

// The latest due date across this project's payment plan(s), Design and
// Supervision. Payment Plan is approved *before* a contract exists, so
// the plan is the fixed input here and the contract's expiry date is
// what has to fit it -- mirrors contract_service._assert_agreement_
// obligations_within_completion_date (the API is the real boundary),
// surfaced here so staff see it before submitting rather than after.
const lastInstallmentDate = computed<string | undefined>(() => {
  const dueDates = (['Design', 'Supervision'] as const).flatMap((stream) => {
    const agreement = paymentStore.getAgreementByProject(projectId.value, stream)
    return agreement ? paymentStore.obligationsForAgreement(agreement.id).map((obligation) => obligation.dueDate) : []
  })
  return dueDates.length > 0 ? dueDates.reduce((latest, date) => (date > latest ? date : latest)) : undefined
})

// Earliest expiry date that's both in the future and on/after the last
// installment.
const minExpiryDate = computed(() => {
  const today = todayIso()
  const last = lastInstallmentDate.value
  return last && last > today ? last : today
})

// Once any contract for this project has ever been signed, its terms
// are locked in -- matches ProjectContractTab.vue's own hasSignedContract.
const hasSignedContract = computed(() => contractStore.contracts.some((contract) => contract.status !== 'Draft'))

function goBack(): void {
  if (project.value) {
    router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: project.value.id }, query: { tab: 'contract' } })
    return
  }
  router.push({ name: ROUTE_NAMES.PROJECTS })
}

// Lets staff jump to any stage of the project, not just back to Contract.
function navigateToTab(tab: ProjectWorkspaceTabKey): void {
  if (!project.value) return
  router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: project.value.id }, query: { tab } })
}

// Auto-filled, read-only -- see the Design & Permit / Supervision date
// fields in the template.
const designPermitPeriod = computed(() => (project.value ? getDesignPermitPeriod(project.value) : undefined))
const supervisionPeriod = computed(() => (project.value ? getSupervisionPeriod(project.value) : undefined))

function displayDate(value: string | null | undefined): string {
  return value ? formatDate(value) : '—'
}

function emptyClause(): ContractClauseInput {
  return { title: '', content: '' }
}

function emptyForm() {
  return {
    currency: 'KWD',
    contractValue: 0,
    expiryDate: '',
    scopeSummary: '',
    clauses: [] as ContractClauseInput[],
  }
}

// Supervision isn't a priced quotation line (it's billed monthly through
// its own payment plan), so a quotation's line items never mention it --
// but the contract does cover it, and with Scope Summary locked there's
// no way to add it by hand. Appended from the project's own picks.
function supervisionScopeLines(project: Project | undefined): string[] {
  return (project?.selectedSupervisionActivities ?? []).map(
    (activity) => `Supervision - ${activity.activityName} (Monthly, ${formatDate(activity.startDate)} to ${formatDate(activity.endDate)})`,
  )
}

// Fallback only, used when the project has no quotation yet: one line
// per picked activity.
function scopeSummaryFromProject(project: Project | undefined): string {
  const lines = (project?.selectedActivities ?? []).map((item) => `${item.serviceName} - ${item.activityName}`)
  return scopeSummaryToHtml([...lines, ...supervisionScopeLines(project)])
}

// Same idea, but from the quotation's own line items -- what was
// actually quoted, more authoritative than the project's raw service
// picks once a quotation exists.
function scopeSummaryFromQuotation(quotation: Quotation, project: Project | undefined): string {
  if (!quotation.lineItems.length) return ''
  return scopeSummaryToHtml([...quotation.lineItems.map((item) => item.description), ...supervisionScopeLines(project)])
}

const form = reactive(emptyForm())
interface ClauseError {
  title?: string
  content?: string
}
const clauseErrors = reactive<ClauseError[]>([])
const { errors, setRules, validateAll } = useFormValidation()

setRules({
  contractValue: [
    validators.required('Contract value is required'),
    () => form.contractValue > 0 || t('project.newContractDialog.contractValueMustBePositive'),
    // Mirrors contract_service._assert_contract_value_matches_quotation
    // (the API is the real boundary) -- surfaced here too so staff see
    // the mismatch immediately instead of only on submit.
    () =>
      !eligibleQuotation.value ||
      form.contractValue === eligibleQuotation.value.amount ||
      t('project.newContractDialog.contractValueMustMatchQuotation', {
        number: eligibleQuotation.value.quotationNo,
        amount: eligibleQuotation.value.amount,
      }),
  ],
  expiryDate: [
    validators.required('Expiry date is required'),
    validators.notPastDate('Expiry date cannot be in the past'),
    () =>
      !form.expiryDate ||
      !lastInstallmentDate.value ||
      form.expiryDate >= lastInstallmentDate.value ||
      t('project.newContractDialog.expiryBeforeLastInstallment', { date: formatDate(lastInstallmentDate.value) }),
  ],
  scopeSummary: [validators.required('Scope summary is required')],
})

// Seeds once the page's own data (project/quotation) has finished
// loading, rather than on every reactive change -- re-seeding after the
// user has started editing would silently discard their in-progress edits.
const isFormSeeded = ref(false)
watch(
  () => [isLoading.value, eligibleQuotation.value, project.value] as const,
  ([loading, quotation, proj]) => {
    if (loading || isFormSeeded.value) return
    // Everything seeded here is locked: contractValue has to match the
    // source quotation's approved amount (see the validator above and
    // contract_service._assert_contract_value_matches_quotation), and
    // scopeSummary/currency simply carry over from it.
    form.contractValue = quotation?.amount ?? proj?.serviceTotal ?? 0
    form.scopeSummary = quotation ? scopeSummaryFromQuotation(quotation, proj) : scopeSummaryFromProject(proj)
    if (quotation) form.currency = quotation.currency
    // Starts on the earliest date that fits the approved payment plan
    // (its last installment) -- still freely changeable to a later one.
    if (lastInstallmentDate.value && lastInstallmentDate.value >= todayIso()) form.expiryDate = lastInstallmentDate.value
    isFormSeeded.value = true
    revalidate()
  },
  { immediate: true },
)

function addClause(): void {
  form.clauses.push(emptyClause())
}

function removeClause(index: number): void {
  form.clauses.splice(index, 1)
}

function revalidate(): void {
  validateAll(form)
}
watch(form, revalidate, { deep: true })

const isSubmitting = ref(false)

async function handleSubmit(): Promise<void> {
  const quotation = eligibleQuotation.value
  if (!quotation) return

  const itemErrors: ClauseError[] = form.clauses.map((clause) => {
    const rowError: ClauseError = {}
    if (!clause.title.trim()) rowError.title = t('project.newContractDialog.clauseTitleRequired')
    if (isRichTextBlank(clause.content)) rowError.content = t('project.newContractDialog.clauseContentRequired')
    return rowError
  })
  clauseErrors.splice(0, clauseErrors.length, ...itemErrors)
  const clausesValid = itemErrors.every((rowError) => Object.keys(rowError).length === 0)

  const formValid = validateAll(form)
  if (!formValid || !clausesValid) return

  isSubmitting.value = true
  try {
    const contract = await contractStore.createContract({
      projectId: projectId.value,
      quotationId: quotation.id,
      currency: form.currency,
      contractValue: form.contractValue,
      expiryDate: form.expiryDate,
      scopeSummary: form.scopeSummary.trim(),
      clauses: form.clauses.map((clause) => ({ title: clause.title.trim(), content: clause.content.trim() })),
    })
    // A contract's mere existence is one of the things "Quotation" ->
    // "Contract" waits on (project_service._assert_stage_exit_criteria).
    await projectStore.refreshProject(projectId.value)
    resultDialogStore.showSuccess(t('project.contractTab.contractCreatedTitle'), t('common.createdSuccessfully', { no: contract.contractNo }))
    goBack()
  } catch (error) {
    resultDialogStore.showError(t('project.contractTab.failedToCreateContract'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <WorkflowProgress
      v-if="project"
      class="no-print"
      :current-stage="project.currentStage"
      :project-status="project.status"
      :includes-design="project.includesDesign"
      :includes-government-submission="project.includesGovernmentSubmission"
      :includes-supervision="project.includesSupervision"
      :selected-activities="project.selectedActivities"
      :selected-permits="project.selectedPermits"
      :selected-supervision-activities="project.selectedSupervisionActivities"
      @navigate-tab="navigateToTab"
    />

    <div v-if="isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="8" />
    </div>

    <EmptyState v-else-if="!project" :title="t('project.workspacePage.notFoundTitle')" :description="t('project.workspacePage.notFoundDescription')" />

    <EmptyState
      v-else-if="hasSignedContract"
      :title="t('project.contractTab.contractAlreadySignedTitle')"
      :description="t('project.contractTab.contractAlreadySignedDescription')"
    />

    <EmptyState
      v-else-if="!eligibleQuotation"
      :title="t('project.contractTab.noEligibleQuotationTitle')"
      :description="t('project.contractTab.noEligibleQuotationDescriptionLong')"
    />

    <Card v-else :padded="true">
      <div class="flex flex-col gap-6">
        <div class="flex flex-col gap-1">
          <div class="flex items-center justify-between">
            <h1 class="text-lg font-semibold text-text-primary">{{ t('project.newContractDialog.title') }}</h1>
            <span class="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700">{{ t('project.newContractDialog.draftPreview') }}</span>
          </div>
          <p class="text-xs text-text-muted">
            {{ t('project.newContractDialog.prefilledFromQuotation', { number: eligibleQuotation.quotationNo }) }}
          </p>
        </div>

        <div class="flex flex-col gap-4 tablet:flex-row tablet:items-start tablet:justify-between">
          <div class="flex items-center gap-3">
            <span class="flex h-11 w-11 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
              <FileSignature class="h-5 w-5" />
            </span>
            <div>
              <p class="text-sm font-semibold text-text-primary">{{ t('common.companyName') }}</p>
              <p class="text-xs text-text-muted">{{ t('project.quotationPreview.companyTagline') }}</p>
            </div>
          </div>
          <p class="text-xs text-text-muted">{{ t('project.newContractDialog.contractNoOnCreation') }}</p>
        </div>

        <Divider />

        <div class="grid grid-cols-1 gap-6 tablet:grid-cols-3">
          <div class="flex flex-col gap-1">
            <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.contractDates.client') }}</p>
            <p class="text-sm font-semibold text-text-primary">{{ client ? getClientFormalName(client) : t('client.unknownClient') }}</p>
          </div>

          <div class="flex flex-col gap-1">
            <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.contractDates.project') }}</p>
            <p class="text-sm font-semibold text-text-primary">{{ project.projectName }} ({{ project.projectNo }})</p>
            <p class="text-sm text-text-muted">{{ project.service }}</p>
          </div>

          <div class="flex flex-col gap-2">
            <TextInput :model-value="formatDate(todayIso())" :label="t('project.newContractDialog.issueDate')" disabled />
            <DatePicker
              v-model="form.expiryDate"
              :label="t('project.newContractDialog.expiryDate')"
              required
              :min="minExpiryDate"
              :hint="lastInstallmentDate ? t('project.newContractDialog.expiryHint', { date: formatDate(lastInstallmentDate) }) : undefined"
              :error="errors.expiryDate"
            />
          </div>
        </div>

        <div v-if="designPermitPeriod || supervisionPeriod" class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <template v-if="designPermitPeriod">
            <TextInput :model-value="displayDate(designPermitPeriod.start)" :label="t('project.contractDates.designPermitStart')" disabled />
            <TextInput :model-value="displayDate(designPermitPeriod.end)" :label="t('project.contractDates.designPermitEnd')" disabled />
          </template>
          <template v-if="supervisionPeriod">
            <TextInput :model-value="displayDate(supervisionPeriod.start)" :label="t('project.contractDates.supervisionStart')" disabled />
            <TextInput :model-value="displayDate(supervisionPeriod.end)" :label="t('project.contractDates.supervisionEnd')" disabled />
          </template>
        </div>

        <Divider />

        <div class="flex flex-col gap-2">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.newContractDialog.scopeSummary') }}</p>
          <div class="rich-text-content rounded-lg border border-border-light bg-bg-secondary px-3 py-2.5 text-sm text-text-secondary" v-html="sanitizeHtml(form.scopeSummary)" />
          <p v-if="errors.scopeSummary" class="text-xs text-danger-500">{{ errors.scopeSummary }}</p>
        </div>

        <div class="flex flex-col gap-2 rounded-lg bg-bg-secondary px-4 py-3">
          <div class="flex items-center justify-between gap-4">
            <span class="text-sm font-medium text-text-secondary">{{ t('project.newContractDialog.contractValue') }}</span>
            <NumberInput
              :model-value="form.contractValue"
              :prefix="form.currency"
              :min="0.01"
              step="0.01"
              class="w-56"
              disabled
              @update:model-value="form.contractValue = Number($event)"
            />
          </div>
          <p v-if="errors.contractValue" class="text-end text-xs text-danger-500">{{ errors.contractValue }}</p>
        </div>

        <div class="flex flex-col gap-3">
          <div class="flex items-center justify-between">
            <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('project.newContractDialog.clausesOptional') }}</p>
            <BaseButton variant="ghost" size="sm" :icon="Plus" @click="addClause">{{ t('project.newContractDialog.addClause') }}</BaseButton>
          </div>

          <div v-for="(clause, index) in form.clauses" :key="index" class="flex flex-col gap-2 rounded-lg border border-border-light p-3">
            <div class="flex items-start gap-2">
              <div class="flex-1">
                <TextInput v-model="clause.title" :placeholder="t('project.newContractDialog.clauseTitlePlaceholder')" :error="clauseErrors[index]?.title" />
              </div>
              <IconButton :icon="Trash2" :label="t('project.newContractDialog.removeClause', { number: index + 1 })" size="sm" @click="removeClause(index)" />
            </div>
            <RichTextEditor v-model="clause.content" :placeholder="t('project.newContractDialog.clauseContentPlaceholder')" :error="clauseErrors[index]?.content" />
          </div>
        </div>
      </div>

      <div class="mt-6 flex justify-end gap-3">
        <BaseButton variant="secondary" :disabled="isSubmitting" @click="goBack">{{ t('common.cancel') }}</BaseButton>
        <BaseButton :loading="isSubmitting" @click="handleSubmit">{{ t('project.newContractDialog.createContract') }}</BaseButton>
      </div>
    </Card>
  </div>
</template>
