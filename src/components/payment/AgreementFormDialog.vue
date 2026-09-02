<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import FormSection from '@/components/common/FormSection.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { getAgreementStreamLabel } from '@/utils/paymentHelpers'
import type { AgreementStream, CreateAgreementInput, PaymentFrequency, PaymentMilestoneInput, PaymentMode } from '@/types/Payment'
import type { SelectOption } from '@/types/Ui'

interface ApprovedContract {
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
  // The project's Signed/Active contract, if it has one -- used to
  // pre-fill Total Contract Amount and Currency instead of leaving them
  // at 0/KWD for the user to re-type from the contract they just
  // approved. undefined for Supervision (which doesn't use these
  // fields) or a project with no approved contract yet.
  approvedContract?: ApprovedContract
}

const props = withDefaults(defineProps<Props>(), { isSubmitting: false, approvedContract: undefined })

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  submit: [input: CreateAgreementInput]
}>()

const PAYMENT_MODE_OPTIONS: SelectOption[] = [
  { label: 'Cash', value: 'Cash' },
  { label: 'Bank Transfer', value: 'Bank Transfer' },
  { label: 'Credit Card', value: 'Credit Card' },
  { label: 'Debit Card', value: 'Debit Card' },
  { label: 'Online Payment', value: 'Online Payment' },
  { label: 'Cheque', value: 'Cheque' },
  { label: 'Other', value: 'Other' },
]

// Design & Permit is billed once -- in full, or split into up to 5
// installments -- never on a recurring interval (that's what
// distinguishes it from Supervision's own separate monthly billing).
// Only ever shown for that stream (see the SelectBox's v-if below), so
// this doesn't need a Supervision-specific variant.
const PAYMENT_FREQUENCY_OPTIONS: SelectOption[] = [
  { label: 'One-time (paid in full)', value: 'One-time' },
  { label: 'Split into installments (up to 5)', value: 'Custom' },
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
const contractReference = ref('')
const paymentMode = ref<PaymentMode>('Bank Transfer')
const paymentFrequency = ref<PaymentFrequency>('Custom')
const milestoneCount = ref(4)
const milestones = ref<PaymentMilestoneInput[]>([])

const isSupervision = computed(() => props.stream === 'Supervision')
const isMilestonePlan = computed(() => !isSupervision.value && paymentFrequency.value === 'Custom')

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

watch(milestoneCount, (count) => {
  milestones.value = buildDefaultMilestones(count)
})

function resetForm(): void {
  contractAmount.value = props.approvedContract?.contractValue ?? 0
  currency.value = props.approvedContract?.currency ?? 'KWD'
  contractStartDate.value = new Date().toISOString().slice(0, 10)
  agreementDate.value = new Date().toISOString().slice(0, 10)
  quotationReference.value = ''
  contractReference.value = ''
  paymentMode.value = 'Bank Transfer'
  paymentFrequency.value = 'Custom'
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

// Supervision's contractAmount/contractStartDate/contractEndDate/
// paymentFrequency are all derived server-side from the project's
// selected Supervision activities (see payment_service.create_agreement)
// -- only agreementDate and paymentMode are ever required from this form
// for that stream.
const canSubmit = computed(() => {
  if (isSupervision.value) return agreementDate.value.length > 0
  const baseValid = contractAmount.value > 0 && contractStartDate.value.length > 0
  return baseValid && (!isMilestonePlan.value || milestonesValid.value)
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
        contractReference: contractReference.value.trim() || undefined,
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
        contractReference: contractReference.value.trim() || undefined,
        paymentMode: paymentMode.value,
        paymentFrequency: paymentFrequency.value,
        milestones: isMilestonePlan.value
          ? milestones.value.map((m) => ({ description: m.description.trim(), percentage: m.percentage, dueDate: m.dueDate }))
          : undefined,
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
    :title="`Create ${getAgreementStreamLabel(stream)} Financial Agreement`"
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
        <TextInput v-model="quotationReference" label="Quotation Reference (optional)" placeholder="QTN-2026-…" />
        <TextInput v-model="contractReference" label="Contract Reference (optional)" placeholder="CNT-2026-…" />
      </div>
    </FormSection>

    <FormSection v-else title="Contract Value" description="The total agreed value of the engagement with this client.">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <NumberInput :model-value="contractAmount" label="Total Contract Amount" :min="0" step="0.01" required @update:model-value="contractAmount = Number($event)" />
        <TextInput v-model="currency" label="Currency" placeholder="KWD" required />
        <DatePicker v-model="agreementDate" label="Agreement Date" required />
        <DatePicker v-model="contractStartDate" label="Contract Start Date" required />
        <TextInput v-model="quotationReference" label="Quotation Reference (optional)" placeholder="QTN-2026-…" />
        <TextInput v-model="contractReference" label="Contract Reference (optional)" placeholder="CNT-2026-…" />
      </div>
    </FormSection>

    <FormSection
      title="Payment Terms"
      :description="isSupervision ? 'Monthly, prorated by day for partial months.' : 'Billed once -- paid in full immediately, or split into up to 5 installments you configure below.'"
    >
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <SelectBox :model-value="paymentMode" label="Payment Mode" :options="PAYMENT_MODE_OPTIONS" @update:model-value="paymentMode = $event as PaymentMode" />
        <SelectBox
          v-if="!isSupervision"
          :model-value="paymentFrequency"
          label="Payment Frequency"
          :options="PAYMENT_FREQUENCY_OPTIONS"
          @update:model-value="paymentFrequency = $event as PaymentFrequency"
        />
      </div>
    </FormSection>

    <FormSection
      v-if="isMilestonePlan"
      title="Milestone Payment Plan"
      description="Choose how many payments the client will make (up to 5), then set each installment's share of the contract amount and its due date. Percentages must add up to 100%."
    >
      <SelectBox
        :model-value="String(milestoneCount)"
        label="Number of Installments"
        :options="INSTALLMENT_COUNT_OPTIONS"
        @update:model-value="milestoneCount = Number($event)"
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
      <FormActionBar submit-label="Create Agreement" :loading="isSubmitting" :disabled="!canSubmit" @submit="handleSubmit" @cancel="handleClose" />
    </template>
  </BaseDialog>
</template>
