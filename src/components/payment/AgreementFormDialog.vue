<script setup lang="ts">
import { Plus, Trash2 } from '@lucide/vue'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import Divider from '@/components/common/Divider.vue'
import IconButton from '@/components/common/IconButton.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useFormValidation } from '@/composables/useFormValidation'
import type { Client } from '@/types/Client'
import type { AgreementStream, CreateAgreementInput, FinancialAgreement, PaymentMilestoneInput, PaymentMode, PaymentObligation } from '@/types/Payment'
import type { Project } from '@/types/Project'
import type { SelectOption } from '@/types/Ui'
import { getClientDisplayName } from '@/utils/clientHelpers'
import { formatCurrency } from '@/utils/currencyFormatter'
import { todayIso } from '@/utils/dateFormatter'
import { validators } from '@/utils/validators'

interface ApprovedQuotation {
  quotationNo: string
  contractValue: number
  currency: string
}

interface Props {
  modelValue: boolean
  projectId: string
  // Same read-only identity context NewQuotationDialog.vue shows at the
  // top of its form -- staff building a payment plan should see which
  // client/project it's for exactly the same way they do when building
  // a quotation, not have to infer it from the panel behind the dialog.
  project?: Project
  client?: Client
  // Which stream this agreement is for -- fixed by the caller (the panel
  // only ever offers "Create Agreement" for a stream this project
  // actually includes and doesn't already have an agreement for), not a
  // choice made inside this dialog.
  stream: AgreementStream
  isSubmitting?: boolean
  // The project's Approved quotation -- always present by the time this
  // dialog can open (a Payment Plan agreement can't be created before
  // one exists, see project_service._assert_stage_exit_criteria's
  // Payment Plan entry criterion), so Quotation Reference/Total Contract
  // Amount/Currency are auto-filled from it rather than left for staff
  // to re-type. undefined only in the impossible-in-practice case of no
  // approved quotation yet.
  approvedContract?: ApprovedQuotation
  // 'edit' prefills every field from existingAgreement/existingObligations
  // and submits an update instead of a create -- only ever offered for a
  // Draft agreement with no payments recorded yet (see
  // payment_service._assert_agreement_editable), same rule the backend
  // enforces regardless of what this dialog does.
  mode?: 'create' | 'edit'
  existingAgreement?: FinancialAgreement
  existingObligations?: PaymentObligation[]
}

const props = withDefaults(defineProps<Props>(), {
  project: undefined,
  client: undefined,
  isSubmitting: false,
  approvedContract: undefined,
  mode: 'create',
  existingAgreement: undefined,
  existingObligations: () => [],
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  submit: [input: CreateAgreementInput]
}>()

const { t } = useI18n()

const isEditMode = computed(() => props.mode === 'edit')

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
// rows on create -- rows are freely added/removed from there on,
// exactly like NewQuotationDialog.vue's line items (no separate "row
// count" control).
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
// One entry per installment, keyed by which field failed -- previously
// a single string per row was always rendered under the Description
// field (same bug as NewQuotationDialog.vue's line items and
// NewContractDialog.vue's clauses), though it could never actually
// surface here: canSubmit already required every one of these same
// per-row conditions before the button would even become clickable.
interface MilestoneError {
  description?: string
  percentage?: string
  dueDate?: string
}
const milestoneErrors = ref<MilestoneError[]>([])
// Shown right under the total when it isn't 100% -- the colored
// "Total: 97%" text alone doesn't actually say 100% is the target, and
// wasn't reachable anyway while canSubmit kept the button disabled with
// no explanation (see handleSubmit below).
const totalError = ref('')

const { errors, setRules, validateAll } = useFormValidation()
setRules({
  agreementDate: [validators.required('Agreement date is required')],
  // Design & Permit only -- Supervision's own contractAmount/
  // contractStartDate are derived server-side, so these two are never
  // actually required from Supervision's own, much shorter form.
  contractAmount: [
    () => isSupervision.value || contractAmount.value > 0 || t('payment.agreementFormDialog.totalAmountRequired'),
  ],
  contractStartDate: [
    () => isSupervision.value || contractStartDate.value.length > 0 || t('payment.agreementFormDialog.contractStartDateRequired'),
  ],
})

const isSupervision = computed(() => props.stream === 'Supervision')
// Design & Permit is always billed as installments now -- 1 installment
// is exactly a single one-time payment, so there's no separate
// "One-time" structure/toggle needed alongside this one.
const isMilestonePlan = computed(() => !isSupervision.value)

function resetForm(): void {
  milestoneErrors.value = []
  totalError.value = ''
  const existing = props.existingAgreement
  if (isEditMode.value && existing) {
    contractAmount.value = existing.contractAmount
    currency.value = existing.currency
    contractStartDate.value = existing.contractStartDate
    agreementDate.value = existing.agreementDate
    quotationReference.value = existing.quotationReference ?? ''
    paymentMode.value = existing.paymentMode
    const rows = [...props.existingObligations].sort((a, b) => a.sequenceNumber - b.sequenceNumber)
    milestones.value = rows.map((obligation) => ({
      description: obligation.description,
      percentage: Math.round((obligation.amountDue / existing.contractAmount) * 10000) / 100,
      dueDate: obligation.dueDate,
    }))
    return
  }

  contractAmount.value = props.approvedContract?.contractValue ?? 0
  currency.value = props.approvedContract?.currency ?? 'KWD'
  contractStartDate.value = new Date().toISOString().slice(0, 10)
  agreementDate.value = new Date().toISOString().slice(0, 10)
  quotationReference.value = props.approvedContract?.quotationNo ?? ''
  paymentMode.value = 'Bank Transfer'
  milestones.value = buildDefaultMilestones()
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) resetForm()
  },
)

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

// Supervision's contractAmount/contractStartDate/contractEndDate are all
// derived server-side from the project's selected Supervision activities
// (see payment_service.create_agreement) -- only agreementDate and
// paymentMode are ever required from this form for that stream, which
// is exactly what the two rules above already account for.
//
// Every field's required-ness (amount, start date, agreement date, and
// every installment's own fields/100% total) is enforced by
// handleSubmit below instead of gating the button itself -- same
// click-then-see-inline-errors pattern as
// NewQuotationDialog.vue/NewContractDialog.vue, rather than a silently
// disabled button with no indication of which field (or whether the
// 100% total) is the actual problem.

function handleSubmit(): void {
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
        projectId: props.projectId,
        stream: props.stream,
        currency: currency.value,
        agreementDate: agreementDate.value,
        quotationReference: quotationReference.value.trim() || undefined,
        paymentMode: paymentMode.value,
      }
    : {
        projectId: props.projectId,
        stream: props.stream,
        contractAmount: contractAmount.value,
        currency: currency.value,
        contractStartDate: contractStartDate.value,
        agreementDate: agreementDate.value,
        quotationReference: quotationReference.value.trim() || undefined,
        paymentMode: paymentMode.value,
        paymentFrequency: 'Custom',
        milestones: milestones.value.map((m) => ({ description: m.description.trim(), percentage: m.percentage, dueDate: m.dueDate })),
      }
  emit('submit', input)
}

function closeDialog(): void {
  emit('update:modelValue', false)
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="isEditMode ? t('payment.agreementFormDialog.editTitle') : t('payment.agreementFormDialog.createTitle')"
    size="lg"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="flex flex-col gap-5">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <TextInput :model-value="client ? getClientDisplayName(client) : ''" :label="t('payment.agreementFormDialog.client')" disabled />
        <TextInput :model-value="project ? `${project.projectName} (${project.projectNo})` : ''" :label="t('payment.agreementFormDialog.project')" disabled />
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
                <SelectBox :model-value="currency" :options="CURRENCY_OPTIONS" @update:model-value="currency = $event" />
              </div>
              <NumberInput
                class="flex-1"
                :model-value="contractAmount"
                :min="0"
                step="0.01"
                required
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

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="isSubmitting" @click="handleSubmit">
        {{ isEditMode ? t('payment.agreementFormDialog.saveChanges') : t('payment.agreementFormDialog.createTitle') }}
      </BaseButton>
    </template>
  </BaseDialog>
</template>
