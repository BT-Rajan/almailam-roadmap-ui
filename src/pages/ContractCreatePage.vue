<script setup lang="ts">
import { ArrowLeft, ArrowRight, Plus, Trash2 } from '@lucide/vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import { useLocale } from '@/composables/useLocale'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useContractStore } from '@/stores/contractStore'
import { usePaymentStore } from '@/stores/paymentStore'
import { useProjectStore } from '@/stores/projectStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { ContractClauseInput } from '@/services/contractService'
import type { Project } from '@/types/Project'
import type { Quotation } from '@/types/Quotation'
import type { SelectOption } from '@/types/Ui'
import { formatDate, todayIso } from '@/utils/dateFormatter'
import { validators } from '@/utils/validators'

// Replaces NewContractDialog.vue's modal -- a dedicated route
// (/projects/:projectId/contract/new), same treatment as
// TaskCreatePage.vue/PaymentPlanFormPage.vue/QuotationCreatePage.vue.
// Create only -- editing an existing contract stays inline on the
// Contract tab (ContractPreview.vue's own @patch).

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isRtl } = useLocale()
const projectStore = useProjectStore()
const quotationStore = useQuotationStore()
const contractStore = useContractStore()
const paymentStore = usePaymentStore()
const resultDialogStore = useResultDialogStore()

const backIcon = computed(() => (isRtl.value ? ArrowRight : ArrowLeft))
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
    paymentStore.agreements.length === 0 ? paymentStore.loadAll() : Promise.resolve(),
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

const CURRENCY_OPTIONS: SelectOption[] = [
  { label: 'KWD', value: 'KWD' },
  { label: 'USD', value: 'USD' },
  { label: 'EUR', value: 'EUR' },
]

function emptyClause(): ContractClauseInput {
  return { title: '', content: '' }
}

function emptyForm() {
  return {
    currency: 'KWD',
    contractValue: 0,
    expiryDate: '',
    clientRepresentative: '',
    scopeSummary: '',
    clauses: [] as ContractClauseInput[],
  }
}

// Prefills contract value from the project's serviceTotal and writes a
// one-line-per-activity scope summary -- fallback only, used when the
// project has no quotation yet.
function scopeSummaryFromProject(project: Project | undefined): string {
  const lines = (project?.selectedActivities ?? []).map((item) => `${item.serviceName} - ${item.activityName}`)
  const supervisionLines = (project?.selectedSupervisionActivities ?? []).map(
    (activity) => `Supervision - ${activity.activityName} (Monthly, ${activity.startDate} to ${activity.endDate})`,
  )
  return [...lines, ...supervisionLines].join('\n')
}

// Same idea, but from the quotation's own line items -- what was
// actually quoted, more authoritative than the project's raw service
// picks once a quotation exists.
function scopeSummaryFromQuotation(quotation: Quotation): string {
  if (!quotation.lineItems.length) return ''
  return quotation.lineItems.map((item) => item.description).join('\n')
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
  clientRepresentative: [validators.required("Client representative's name is required")],
  scopeSummary: [validators.required('Scope summary is required')],
})

// Seeds once the page's own data (project/quotation/client) has finished
// loading, rather than on every reactive change -- re-seeding after the
// user has started editing would silently discard their in-progress edits.
const isFormSeeded = ref(false)
watch(
  () => [isLoading.value, eligibleQuotation.value, project.value, client.value] as const,
  ([loading, quotation, proj, clientValue]) => {
    if (loading || isFormSeeded.value) return
    // A sensible starting point -- clientRepresentative/scopeSummary
    // can still be changed freely. contractValue can't: it has to match
    // the source quotation's approved amount (see the validator above
    // and contract_service._assert_contract_value_matches_quotation);
    // it's pre-filled here purely so staff aren't asked to retype it.
    form.clientRepresentative = clientValue?.contactPerson || ''
    form.contractValue = quotation?.amount ?? proj?.serviceTotal ?? 0
    form.scopeSummary = quotation ? scopeSummaryFromQuotation(quotation) : scopeSummaryFromProject(proj)
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
    if (!clause.content.trim()) rowError.content = t('project.newContractDialog.clauseContentRequired')
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
      clientRepresentative: form.clientRepresentative.trim(),
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
    <BaseButton variant="ghost" size="sm" :icon="backIcon" class="self-start no-print" @click="goBack">
      {{ t('project.newContractDialog.backToContract') }}
    </BaseButton>

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

    <div v-else class="rounded-xl border border-border-light bg-bg-card p-5">
      <h1 class="mb-4 text-lg font-semibold text-text-primary">{{ t('project.newContractDialog.title') }}</h1>

      <div class="flex flex-col gap-5">
        <p class="text-xs text-text-muted">
          {{ t('project.newContractDialog.prefilledFromQuotation', { number: eligibleQuotation.quotationNo }) }}
        </p>

        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-3">
          <SelectBox v-model="form.currency" :label="t('project.newContractDialog.currency')" :options="CURRENCY_OPTIONS" disabled />
          <NumberInput
            :model-value="form.contractValue"
            :label="t('project.newContractDialog.contractValue')"
            :min="0.01"
            step="0.01"
            required
            disabled
            :error="errors.contractValue"
            @update:model-value="form.contractValue = Number($event)"
          />
          <DatePicker
            v-model="form.expiryDate"
            :label="t('project.newContractDialog.expiryDate')"
            required
            :min="minExpiryDate"
            :hint="lastInstallmentDate ? t('project.newContractDialog.expiryHint', { date: formatDate(lastInstallmentDate) }) : undefined"
            :error="errors.expiryDate"
          />
        </div>

        <TextInput
          v-model="form.clientRepresentative"
          :label="t('project.newContractDialog.clientRepresentative')"
          :placeholder="t('project.newContractDialog.clientRepresentativePlaceholder')"
          required
          :error="errors.clientRepresentative"
        />

        <TextArea
          v-model="form.scopeSummary"
          :label="t('project.newContractDialog.scopeSummary')"
          :placeholder="t('project.newContractDialog.scopeSummaryPlaceholder')"
          :rows="3"
          required
          :error="errors.scopeSummary"
        />

        <div class="flex flex-col gap-3">
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-text-secondary">{{ t('project.newContractDialog.clausesOptional') }}</label>
            <BaseButton variant="ghost" size="sm" :icon="Plus" @click="addClause">{{ t('project.newContractDialog.addClause') }}</BaseButton>
          </div>

          <div v-for="(clause, index) in form.clauses" :key="index" class="flex flex-col gap-2 rounded-lg border border-border-light p-3">
            <div class="flex items-start gap-2">
              <div class="flex-1">
                <TextInput v-model="clause.title" :placeholder="t('project.newContractDialog.clauseTitlePlaceholder')" :error="clauseErrors[index]?.title" />
              </div>
              <IconButton :icon="Trash2" :label="t('project.newContractDialog.removeClause', { number: index + 1 })" size="sm" @click="removeClause(index)" />
            </div>
            <TextArea v-model="clause.content" :placeholder="t('project.newContractDialog.clauseContentPlaceholder')" :rows="2" :error="clauseErrors[index]?.content" />
          </div>
        </div>
      </div>

      <div class="mt-6 flex justify-end gap-3">
        <BaseButton variant="secondary" :disabled="isSubmitting" @click="goBack">{{ t('common.cancel') }}</BaseButton>
        <BaseButton :loading="isSubmitting" @click="handleSubmit">{{ t('project.newContractDialog.createContract') }}</BaseButton>
      </div>
    </div>
  </div>
</template>
