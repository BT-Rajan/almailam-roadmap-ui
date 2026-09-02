<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import FormSection from '@/components/common/FormSection.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import type { AgreementStream, CreateAgreementInput, FinancialAgreement, PaymentMilestoneInput, PaymentMode, PaymentObligation } from '@/types/Payment'
import type { SelectOption } from '@/types/Ui'

interface ApprovedQuotation {
  quotationNo: string
  contractValue: number
  currency: string
}

interface Props {
  modelValue: boolean
  projectId: string
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

const isEditMode = computed(() => props.mode === 'edit')

const PAYMENT_MODE_OPTIONS: SelectOption[] = [
  { label: 'Cash', value: 'Cash' },
  { label: 'Bank Transfer', value: 'Bank Transfer' },
  { label: 'Credit Card', value: 'Credit Card' },
  { label: 'Debit Card', value: 'Debit Card' },
  { label: 'Online Payment', value: 'Online Payment' },
  { label: 'Cheque', value: 'Cheque' },
  { label: 'Other', value: 'Other' },
]

const CURRENCY_OPTIONS: SelectOption[] = [
  { label: 'KWD', value: 'KWD' },
  { label: 'USD', value: 'USD' },
  { label: 'EUR', value: 'EUR' },
]

const INSTALLMENT_COUNT_OPTIONS: SelectOption[] = [1, 2, 3, 4, 5].map((n) => ({ label: String(n), value: String(n) }))

// The default 4-installment plan requested for this project: 25% at
// signup, 25% when the design is approved, 25% when the approval is
// filed, and the balance (folded into the last row so rounding never
// leaves a gap) at handover. Used to seed the milestone rows the
// moment "Milestone plan" is picked or the count is changed to 4 --
// still fully editable afterward.
const DEFAULT_FOUR_MILESTONE_LABELS = ['At signup', 'On design approval', 'On approval filed', 'At handover to client']

const contractAmount = ref(0)
const currency = ref('KWD')
const contractStartDate = ref(new Date().toISOString().slice(0, 10))
const agreementDate = ref(new Date().toISOString().slice(0, 10))
const quotationReference = ref('')
const paymentMode = ref<PaymentMode>('Bank Transfer')
const milestoneCount = ref(4)
const milestones = ref<PaymentMilestoneInput[]>([])

const isSupervision = computed(() => props.stream === 'Supervision')
// Design & Permit is always billed as installments now -- 1 installment
// is exactly a single one-time payment (generate_milestone_schedule
// puts 100% of the contract amount on that one row), so there's no
// separate "One-time" structure/toggle needed alongside this one.
const isMilestonePlan = computed(() => !isSupervision.value)

function evenSplitPercentages(count: number): number[] {
  const base = Math.floor((100 / count) * 100) / 100
  const percentages = Array<number>(count).fill(base)
  percentages[count - 1] = Math.round((100 - base * (count - 1)) * 100) / 100
  return percentages
}

function buildDefaultMilestones(count: number): PaymentMilestoneInput[] {
  const percentages = count === 4 ? [25, 25, 25, 25] : evenSplitPercentages(count)
  return percentages.map((percentage, index) => ({
    description: count === 4 ? DEFAULT_FOUR_MILESTONE_LABELS[index] : `Installment ${index + 1}`,
    percentage,
    dueDate: '',
  }))
}

// Bound directly to the "Number of Installments" SelectBox rather than a
// watch(milestoneCount, ...) -- a watcher would also fire (and clobber
// the real prefilled rows with fresh defaults) the moment resetForm's
// edit-mode branch sets milestoneCount.value from existingObligations.
function handleMilestoneCountChange(count: number): void {
  milestoneCount.value = count
  milestones.value = buildDefaultMilestones(count)
}

function resetForm(): void {
  const existing = props.existingAgreement
  if (isEditMode.value && existing) {
    contractAmount.value = existing.contractAmount
    currency.value = existing.currency
    contractStartDate.value = existing.contractStartDate
    agreementDate.value = existing.agreementDate
    quotationReference.value = existing.quotationReference ?? ''
    paymentMode.value = existing.paymentMode
    const rows = [...props.existingObligations].sort((a, b) => a.sequenceNumber - b.sequenceNumber)
    milestoneCount.value = rows.length || 1
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
  milestoneCount.value = 4
  milestones.value = buildDefaultMilestones(4)
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) resetForm()
  },
)

const milestoneTotal = computed(() => Math.round(milestones.value.reduce((sum, m) => sum + (m.percentage || 0), 0) * 100) / 100)
const milestonesValid = computed(
  () =>
    milestones.value.length > 0 &&
    milestones.value.length <= 5 &&
    Math.abs(milestoneTotal.value - 100) <= 0.5 &&
    milestones.value.every((m) => m.description.trim().length > 0 && m.dueDate.length > 0 && m.percentage > 0),
)

// Supervision's contractAmount/contractStartDate/contractEndDate are all
// derived server-side from the project's selected Supervision activities
// (see payment_service.create_agreement) -- only agreementDate and
// paymentMode are ever required from this form for that stream.
const canSubmit = computed(() => {
  if (isSupervision.value) return agreementDate.value.length > 0
  const baseValid = contractAmount.value > 0 && contractStartDate.value.length > 0
  return baseValid && milestonesValid.value
})

function handleSubmit(): void {
  if (!canSubmit.value) return
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

function handleClose(): void {
  emit('update:modelValue', false)
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="isEditMode ? 'Edit Payment Plan' : 'Create Payment Plan'"
    size="lg"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <FormSection
      v-if="isSupervision"
      title="Supervision Billing"
      description="The contract amount and payment schedule are generated automatically -- one prorated obligation per calendar month -- from this project's selected Supervision activities and their dates."
    >
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <TextInput v-model="currency" label="Currency" placeholder="KWD" required />
        <DatePicker v-model="agreementDate" label="Agreement Date" required />
        <TextInput
          v-model="quotationReference"
          label="Quotation Reference"
          disabled
          hint="Auto-filled from this project's approved quotation."
        />
      </div>
    </FormSection>

    <FormSection v-else title="Payment Plan" description="The total amount and installment schedule for this payment plan.">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <div class="flex flex-col gap-1.5">
          <label class="text-sm font-medium text-text-secondary">Total Amount <span class="text-danger-500">*</span></label>
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
              @update:model-value="contractAmount = Number($event)"
            />
          </div>
        </div>
        <DatePicker v-model="agreementDate" label="Agreement Date" required />
        <DatePicker v-model="contractStartDate" label="Contract Start Date" required />
        <TextInput
          v-model="quotationReference"
          label="Quotation Reference"
          disabled
          hint="Auto-filled from this project's approved quotation."
        />
      </div>
    </FormSection>

    <FormSection
      title="Payment Mode"
      :description="isSupervision ? 'Monthly, prorated by day for partial months.' : 'How this will be paid -- the installment schedule is set below.'"
    >
      <SelectBox :model-value="paymentMode" label="Payment Mode" :options="PAYMENT_MODE_OPTIONS" @update:model-value="paymentMode = $event as PaymentMode" />
    </FormSection>

    <FormSection
      v-if="isMilestonePlan"
      title="Installments"
      description="Choose how many payments the client will make (1 for a single one-time payment, up to 5), then set each installment's share of the contract amount and its due date. Percentages must add up to 100%."
    >
      <SelectBox
        :model-value="String(milestoneCount)"
        label="Number of Installments"
        :options="INSTALLMENT_COUNT_OPTIONS"
        @update:model-value="handleMilestoneCountChange(Number($event))"
      />

      <div class="mt-3 flex flex-col gap-2">
        <div v-for="(milestone, index) in milestones" :key="index" class="grid grid-cols-1 gap-2 rounded-lg border border-border-light p-3 tablet:grid-cols-[2fr_1fr_1fr]">
          <TextInput v-model="milestone.description" :label="`Installment ${index + 1}`" placeholder="e.g. At signup" />
          <NumberInput :model-value="milestone.percentage" label="% of Contract" :min="0" :max="100" step="0.01" @update:model-value="milestone.percentage = Number($event)" />
          <DatePicker v-model="milestone.dueDate" label="Due Date" required />
        </div>
      </div>

      <p class="mt-2 text-xs" :class="Math.abs(milestoneTotal - 100) <= 0.5 ? 'text-text-muted' : 'font-medium text-danger-600'">
        Total: {{ milestoneTotal }}% {{ Math.abs(milestoneTotal - 100) <= 0.5 ? '' : '(must add up to 100%)' }}
      </p>
    </FormSection>

    <template #footer>
      <FormActionBar
        :submit-label="isEditMode ? 'Save Changes' : 'Create Payment Plan'"
        :loading="isSubmitting"
        :disabled="!canSubmit"
        @submit="handleSubmit"
        @cancel="handleClose"
      />
    </template>
  </BaseDialog>
</template>
