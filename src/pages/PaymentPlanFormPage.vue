<script setup lang="ts">
import { ArrowLeft, ArrowRight, Plus, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import Divider from '@/components/common/Divider.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextInput from '@/components/common/TextInput.vue'
import { usePaymentAgreements } from '@/composables/usePaymentAgreements'
import { useFormValidation } from '@/composables/useFormValidation'
import { useLocale } from '@/composables/useLocale'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useProjectStore } from '@/stores/projectStore'
import { usePaymentStore } from '@/stores/paymentStore'
import { useQuotationStore } from '@/stores/quotationStore'
import { useResultDialogStore } from '@/stores/resultDialogStore'
import type { AgreementStream, CreateAgreementInput, PaymentMilestoneInput, PaymentMode } from '@/types/Payment'
import type { Project } from '@/types/Project'
import type { SelectOption } from '@/types/Ui'
import { getClientDisplayName } from '@/utils/clientHelpers'
import { formatCurrency } from '@/utils/currencyFormatter'
import { todayIso } from '@/utils/dateFormatter'
import { validators } from '@/utils/validators'

// Replaces AgreementFormDialog.vue's modal -- a dedicated route
// (/projects/:projectId/payment-plan/:stream), same treatment as
// TaskCreatePage.vue replacing TaskFormDialog.vue. Create vs edit isn't
// a caller-chosen mode here: it's simply whether this project's given
// stream already has an agreement (usePaymentAgreements.agreementForStream).

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isRtl } = useLocale()
const projectStore = useProjectStore()
const paymentStore = usePaymentStore()
const quotationStore = useQuotationStore()
const resultDialogStore = useResultDialogStore()

const backIcon = computed(() => (isRtl.value ? ArrowRight : ArrowLeft))

const projectId = computed(() => route.params.projectId as string)
const VALID_STREAMS: AgreementStream[] = ['Design', 'Supervision']
const stream = computed<AgreementStream | undefined>(() => {
  const value = route.params.stream as string
  return VALID_STREAMS.includes(value as AgreementStream) ? (value as AgreementStream) : undefined
})

const isLoading = ref(true)

async function loadData(): Promise<void> {
  isLoading.value = true
  if (projectStore.projects.length === 0) await projectStore.loadProjects()
  if (paymentStore.agreements.length === 0) await paymentStore.loadAll()
  await quotationStore.loadQuotationsForProject(projectId.value)
  isLoading.value = false
}
onMounted(loadData)
watch(projectId, loadData)

const project = computed(() => projectStore.getProjectById(projectId.value))
const client = computed(() => (project.value ? projectStore.getClientById(project.value.clientId) : undefined))

// usePaymentAgreements reads project.includesDesign/includesSupervision
// synchronously as soon as it's called (its own onMounted fires before
// this page's loadData() above has actually resolved a project) -- fall
// back to an empty object rather than project.value! so that doesn't
// throw while the project is still loading; agreementForStream/
// obligationsForStream below don't depend on those two flags anyway.
const { agreementForStream, obligationsForStream } = usePaymentAgreements(
  () => projectId.value,
  () => project.value ?? ({} as Project),
)

const existingAgreement = computed(() => (stream.value ? agreementForStream(stream.value) : undefined))
const existingObligations = computed(() => (stream.value ? obligationsForStream(stream.value) : []))
const isEditMode = computed(() => !!existingAgreement.value)

// The project's Approved quotation -- always present by the time this
// page can be reached (a Payment Plan agreement can't be created before
// one exists, see project_service._assert_stage_exit_criteria's Payment
// Plan entry criterion), so Quotation Reference/Total Amount/Currency
// are auto-filled from it rather than left for staff to re-type.
const approvedQuotation = computed(() => quotationStore.quotations.find((quotation) => quotation.status === 'Approved'))

function goBack(): void {
  if (project.value) {
    router.push({ name: ROUTE_NAMES.PROJECT_WORKSPACE, params: { projectId: project.value.id }, query: { tab: 'payment-plan' } })
    return
  }
  router.push({ name: ROUTE_NAMES.PROJECTS })
}

const PAYMENT_MODE_OPTIONS: SelectOption[] = [
  { label: 'Cash', value: 'Cash', labelKey: 'payment.paymentMode.cash' },
  { label: 'Bank Transfer', value: 'Bank Transfer', labelKey: 'payment.paymentMode.bankTransfer' },
  { label: 'Credit Card', value: 'Credit Card', labelKey: 'payment.paymentMode.creditCard' },
  { label: 'Debit Card', value: 'Debit Card', labelKey: 'payment.paymentMode.debitCard' },
  { label: 'Online Payment', value: 'Online Payment', labelKey: 'payment.paymentMode.onlinePayment' },
  { label: 'Cheque', value: 'Cheque', labelKey: 'payment.paymentMode.cheque' },
  { label: 'Other', value: 'Other', labelKey: 'payment.paymentMode.other' },
]

const CURRENCY_OPTIONS: SelectOption[] = [
  { label: 'KWD', value: 'KWD' },
  { label: 'USD', value: 'USD' },
  { label: 'EUR', value: 'EUR' },
]

// The default 4-installment plan requested for this project: 25% at
// signup, 25% when the design is approved, 25% when the approval is
// filed, and the balance at handover. Used only to seed the initial
// rows on create -- rows are freely added/removed from there on.
const DEFAULT_FOUR_MILESTONE_LABELS = ['At signup', 'On design approval', 'On approval filed', 'At handover to client']
const MAX_MILESTONES = 5

function buildDefaultMilestones(): PaymentMilestoneInput[] {
  return DEFAULT_FOUR_MILESTONE_LABELS.map((description) => ({ description, percentage: 25, dueDate: '' }))
}

const contractAmount = ref(0)
const currency = ref('KWD')
const contractStartDate = ref(new Date().toISOString().slice(0, 10))
const agreementDate = ref(new Date().toISOString().slice(0, 10))
const quotationReference = ref('')
const paymentMode = ref<PaymentMode>('Bank Transfer')
const milestones = ref<PaymentMilestoneInput[]>([])
interface MilestoneError {
  description?: string
  percentage?: string
  dueDate?: string
}
const milestoneErrors = ref<MilestoneError[]>([])
const totalError = ref('')
// True once the form's own fields have been seeded from
// existingAgreement/approvedQuotation -- guards against re-seeding on
// every reactive change while still waiting on those to load.
const isFormSeeded = ref(false)

const { errors, setRules, validateAll } = useFormValidation()
setRules({
  agreementDate: [validators.required('Agreement date is required')],
  contractAmount: [
    () => isSupervision.value || contractAmount.value > 0 || t('payment.agreementFormDialog.totalAmountRequired'),
    // Mirrors payment_service._assert_design_amount_matches_quotation
    // (the API is the real boundary) -- surfaced here too so staff see
    // the mismatch immediately instead of only on submit. Supervision
    // isn't checked, same as the backend: its billing comes from
    // selected Supervision activities, not the quotation total.
    () =>
      isSupervision.value ||
      !approvedQuotation.value ||
      contractAmount.value === approvedQuotation.value.amount ||
      t('payment.agreementFormDialog.totalAmountMustMatchQuotation', {
        number: approvedQuotation.value.quotationNo,
        amount: approvedQuotation.value.amount,
      }),
  ],
  contractStartDate: [
    () => isSupervision.value || contractStartDate.value.length > 0 || t('payment.agreementFormDialog.contractStartDateRequired'),
  ],
})

const isSupervision = computed(() => stream.value === 'Supervision')
// Design & Permit is always billed as installments now -- 1 installment
// is exactly a single one-time payment, so there's no separate
// "One-time" structure/toggle needed alongside this one.
const isMilestonePlan = computed(() => !isSupervision.value)

function seedForm(): void {
  milestoneErrors.value = []
  totalError.value = ''
  const existing = existingAgreement.value
  if (existing) {
    contractAmount.value = existing.contractAmount
    currency.value = existing.currency
    contractStartDate.value = existing.contractStartDate
    agreementDate.value = existing.agreementDate
    // Prefer the real quotationNo (from quotation_id, migration 0100)
    // over the legacy free-text quotationReference -- only falls back
    // to the latter for an agreement that predates quotation_id.
    quotationReference.value = existing.quotationNo ?? existing.quotationReference ?? ''
    paymentMode.value = existing.paymentMode
    const rows = [...existingObligations.value].sort((a, b) => a.sequenceNumber - b.sequenceNumber)
    milestones.value = rows.map((obligation) => ({
      description: obligation.description,
      percentage: Math.round((obligation.amountDue / existing.contractAmount) * 10000) / 100,
      dueDate: obligation.dueDate,
    }))
    isFormSeeded.value = true
    return
  }

  // Locked to the approved quotation's amount/currency while creating
  // (see payment_service._assert_design_amount_matches_quotation) --
  // editable again once existingAgreement exists (isEditMode), only so
  // a legacy mismatch can be corrected back into agreement with it.
  contractAmount.value = approvedQuotation.value?.amount ?? 0
  currency.value = approvedQuotation.value?.currency ?? 'KWD'
  contractStartDate.value = new Date().toISOString().slice(0, 10)
  agreementDate.value = new Date().toISOString().slice(0, 10)
  quotationReference.value = approvedQuotation.value?.quotationNo ?? ''
  paymentMode.value = 'Bank Transfer'
  milestones.value = buildDefaultMilestones()
  isFormSeeded.value = true
}

// Same "highlight empty mandatory fields immediately" fix as
// NewProjectWizardPage.vue -- flagged red from the moment the form is
// shown instead of only after a failed submit.
function revalidate(): void {
  validateAll({
    agreementDate: agreementDate.value,
    contractAmount: contractAmount.value,
    contractStartDate: contractStartDate.value,
  })
}

// Seeds once the page's own data (project/agreement/obligations/
// approved quotation) has finished loading, rather than on every
// reactive change to those -- re-seeding after the user has started
// editing would silently discard their in-progress edits.
watch(
  () => [isLoading.value, existingAgreement.value, approvedQuotation.value] as const,
  ([loading]) => {
    if (loading || isFormSeeded.value) return
    seedForm()
    revalidate()
  },
  { immediate: true },
)
watch([agreementDate, contractAmount, contractStartDate], revalidate)

function addMilestone(): void {
  if (milestones.value.length >= MAX_MILESTONES) return
  milestones.value.push({ description: '', percentage: 0, dueDate: '' })
}

function removeMilestone(index: number): void {
  if (milestones.value.length === 1) return // always keep at least one row
  milestones.value.splice(index, 1)
}

function milestoneAmount(milestone: PaymentMilestoneInput): number {
  return contractAmount.value * ((milestone.percentage || 0) / 100)
}

const milestoneTotal = computed(() => Math.round(milestones.value.reduce((sum, m) => sum + (m.percentage || 0), 0) * 100) / 100)
const milestoneTotalValid = computed(() => Math.abs(milestoneTotal.value - 100) <= 0.5)

const isSubmitting = ref(false)

async function handleSubmit(): Promise<void> {
  if (!stream.value) return
  const formValid = validateAll({
    agreementDate: agreementDate.value,
    contractAmount: contractAmount.value,
    contractStartDate: contractStartDate.value,
  })

  let rowsValid = true
  if (isMilestonePlan.value) {
    const itemErrors: MilestoneError[] = milestones.value.map((m) => {
      const rowError: MilestoneError = {}
      if (!m.description.trim()) rowError.description = t('payment.agreementFormDialog.descriptionRequired')
      if (m.percentage <= 0) rowError.percentage = t('payment.agreementFormDialog.percentageRequired')
      if (!m.dueDate) rowError.dueDate = t('payment.agreementFormDialog.dueDateRequired')
      return rowError
    })
    milestoneErrors.value = itemErrors
    totalError.value = milestoneTotalValid.value ? '' : t('payment.agreementFormDialog.totalMustEqual100', { percent: milestoneTotal.value })
    rowsValid = itemErrors.every((rowError) => Object.keys(rowError).length === 0) && milestoneTotalValid.value
  }

  if (!formValid || !rowsValid) return

  const input: CreateAgreementInput = isSupervision.value
    ? {
        projectId: projectId.value,
        stream: stream.value,
        currency: currency.value,
        agreementDate: agreementDate.value,
        quotationReference: quotationReference.value.trim() || undefined,
        paymentMode: paymentMode.value,
      }
    : {
        projectId: projectId.value,
        stream: stream.value,
        contractAmount: contractAmount.value,
        currency: currency.value,
        contractStartDate: contractStartDate.value,
        agreementDate: agreementDate.value,
        quotationReference: quotationReference.value.trim() || undefined,
        paymentMode: paymentMode.value,
        paymentFrequency: 'Custom',
        milestones: milestones.value.map((m) => ({ description: m.description.trim(), percentage: m.percentage, dueDate: m.dueDate })),
      }

  isSubmitting.value = true
  try {
    if (isEditMode.value && existingAgreement.value) {
      await paymentStore.updateAgreement(existingAgreement.value.id, input)
      resultDialogStore.showSuccess(t('payment.planPanel.planUpdatedTitle'), t('payment.planPanel.planUpdatedDescription'))
    } else {
      await paymentStore.createAgreement(input, 'Rajan Kumar')
      resultDialogStore.showSuccess(t('payment.planPanel.planCreatedTitle'), t('payment.planPanel.planCreatedDescription'))
    }
    goBack()
  } catch (error) {
    resultDialogStore.showError(t('payment.planPanel.couldNotSave'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <BaseButton variant="ghost" size="sm" :icon="backIcon" class="self-start no-print" @click="goBack">
      {{ t('payment.agreementFormDialog.backToPaymentPlan') }}
    </BaseButton>

    <div v-if="isLoading" class="max-w-3xl rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="8" />
    </div>

    <EmptyState
      v-else-if="!project || !stream"
      :title="t('payment.agreementFormDialog.planNotFoundTitle')"
      :description="t('payment.agreementFormDialog.planNotFoundDescription')"
    />

    <div v-else class="max-w-3xl rounded-xl border border-border-light bg-bg-card p-5">
      <h1 class="mb-4 text-lg font-semibold text-text-primary">
        {{ isEditMode ? t('payment.agreementFormDialog.editTitle') : t('payment.agreementFormDialog.createTitle') }}
      </h1>

      <div class="flex flex-col gap-5">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput :model-value="client ? getClientDisplayName(client) : ''" :label="t('payment.agreementFormDialog.client')" disabled />
          <TextInput :model-value="`${project.projectName} (${project.projectNo})`" :label="t('payment.agreementFormDialog.project')" disabled />
        </div>

        <DatePicker v-model="agreementDate" :label="t('payment.agreementFormDialog.agreementDate')" required :max="todayIso()" :error="errors.agreementDate" />

        <div v-if="isSupervision" class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput v-model="currency" :label="t('payment.agreementFormDialog.currency')" placeholder="KWD" required />
          <TextInput
            v-model="quotationReference"
            :label="t('payment.agreementFormDialog.quotationReference')"
            disabled
            :hint="t('payment.agreementFormDialog.quotationReferenceHint')"
          />
        </div>

        <template v-else>
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <div class="flex flex-col gap-1.5">
              <label class="text-sm font-medium text-text-secondary">{{ t('payment.agreementFormDialog.totalAmount') }} <span class="text-danger-500">*</span></label>
              <div class="flex gap-2">
                <div class="w-24 shrink-0">
                  <SelectBox :model-value="currency" :options="CURRENCY_OPTIONS" :disabled="!isEditMode" @update:model-value="currency = $event" />
                </div>
                <NumberInput
                  class="flex-1"
                  :model-value="contractAmount"
                  :min="0"
                  step="0.01"
                  required
                  :disabled="!isEditMode"
                  :error="errors.contractAmount"
                  @update:model-value="contractAmount = Number($event)"
                />
              </div>
            </div>
            <DatePicker v-model="contractStartDate" :label="t('payment.agreementFormDialog.contractStartDate')" required :max="todayIso()" :error="errors.contractStartDate" />
          </div>

          <TextInput
            v-model="quotationReference"
            :label="t('payment.agreementFormDialog.quotationReference')"
            disabled
            :hint="t('payment.agreementFormDialog.quotationReferenceHint')"
          />
        </template>

        <SelectBox :model-value="paymentMode" :label="t('payment.agreementFormDialog.paymentModeTitle')" :options="PAYMENT_MODE_OPTIONS" @update:model-value="paymentMode = $event as PaymentMode" />

        <div v-if="isMilestonePlan" class="flex flex-col gap-3">
          <div class="flex items-center justify-between">
            <label class="text-sm font-medium text-text-secondary">{{ t('payment.agreementFormDialog.installments') }}</label>
            <BaseButton variant="ghost" size="sm" :icon="Plus" :disabled="milestones.length >= MAX_MILESTONES" @click="addMilestone">
              {{ t('payment.agreementFormDialog.addInstallment') }}
            </BaseButton>
          </div>

          <div class="overflow-x-auto rounded-lg border border-border-light">
            <table class="w-full min-w-[560px] border-collapse">
              <thead>
                <tr class="border-b border-border-light bg-bg-secondary">
                  <th class="px-3 py-2.5 text-start text-xs font-semibold uppercase tracking-wide text-text-muted">
                    {{ t('payment.agreementFormDialog.columnInstallment') }}
                  </th>
                  <th class="w-24 px-3 py-2.5 text-end text-xs font-semibold uppercase tracking-wide text-text-muted">
                    {{ t('payment.agreementFormDialog.columnPercent') }}
                  </th>
                  <th class="w-36 px-3 py-2.5 text-end text-xs font-semibold uppercase tracking-wide text-text-muted">
                    {{ t('payment.agreementFormDialog.columnDueDate') }}
                  </th>
                  <th class="w-32 px-3 py-2.5 text-end text-xs font-semibold uppercase tracking-wide text-text-muted">
                    {{ t('payment.agreementFormDialog.columnAmount') }}
                  </th>
                  <th class="w-10 px-2 py-2.5"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(milestone, index) in milestones" :key="index" class="border-b border-border-light last:border-0">
                  <td class="px-3 py-2 align-top">
                    <TextInput v-model="milestone.description" :placeholder="t('payment.agreementFormDialog.installmentPlaceholder')" :error="milestoneErrors[index]?.description" />
                  </td>
                  <td class="px-3 py-2 align-top">
                    <NumberInput
                      :model-value="milestone.percentage"
                      :min="0"
                      :max="100"
                      step="0.01"
                      :error="milestoneErrors[index]?.percentage"
                      @update:model-value="milestone.percentage = Number($event)"
                    />
                  </td>
                  <td class="px-3 py-2 align-top">
                    <DatePicker v-model="milestone.dueDate" :error="milestoneErrors[index]?.dueDate" />
                  </td>
                  <td class="px-3 py-2 text-end align-top">
                    <span class="inline-block pt-2 text-sm font-medium text-text-primary">{{ formatCurrency(milestoneAmount(milestone), currency) }}</span>
                  </td>
                  <td class="px-2 py-2 text-end align-top">
                    <IconButton
                      :icon="Trash2"
                      :label="t('payment.agreementFormDialog.removeInstallment', { number: index + 1 })"
                      size="sm"
                      :disabled="milestones.length === 1"
                      @click="removeMilestone(index)"
                    />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <Divider v-if="isMilestonePlan" />

        <div v-if="isMilestonePlan" class="flex flex-col gap-2 text-sm">
          <div class="flex items-center justify-between text-text-secondary">
            <span>{{ t('payment.agreementFormDialog.milestoneTotal') }}</span>
            <span :class="milestoneTotalValid ? 'font-medium text-text-primary' : 'font-medium text-danger-600'">{{ t('payment.agreementFormDialog.total', { percent: milestoneTotal }) }}</span>
          </div>
          <p v-if="totalError" class="text-xs text-danger-700">{{ totalError }}</p>
          <Divider />
          <div class="flex items-center justify-between">
            <span class="text-sm font-semibold text-text-primary">{{ t('payment.agreementFormDialog.totalAmount') }}</span>
            <span class="text-lg font-semibold text-primary-700">{{ formatCurrency(contractAmount, currency) }}</span>
          </div>
        </div>
      </div>

      <div class="mt-6 flex justify-end gap-3">
        <BaseButton variant="secondary" :disabled="isSubmitting" @click="goBack">{{ t('common.cancel') }}</BaseButton>
        <BaseButton :loading="isSubmitting" @click="handleSubmit">
          {{ isEditMode ? t('payment.agreementFormDialog.saveChanges') : t('payment.agreementFormDialog.createTitle') }}
        </BaseButton>
      </div>
    </div>
  </div>
</template>
