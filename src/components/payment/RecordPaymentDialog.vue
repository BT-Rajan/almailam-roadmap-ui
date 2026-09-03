<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import BaseDialog from '@/components/common/BaseDialog.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import FormSection from '@/components/common/FormSection.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { formatCurrency } from '@/utils/currencyFormatter'
import { getObligationAmountPending } from '@/utils/paymentHelpers'
import type { PaymentMode, PaymentObligation, RecordPaymentInput } from '@/types/Payment'
import type { SelectOption } from '@/types/Ui'

interface Props {
  modelValue: boolean
  agreementId: string
  projectId: string
  currency: string
  outstandingObligations: PaymentObligation[]
  preselectedObligationId?: string
  isSubmitting?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  preselectedObligationId: undefined,
  isSubmitting: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  // proofFile is sent as a separate follow-up multipart request (see
  // paymentService.attachPaymentProof) once the payment itself exists --
  // RecordPaymentInput stays a plain JSON body.
  submit: [input: RecordPaymentInput, proofFile: File | undefined]
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

const amountReceived = ref(0)
const paymentDate = ref(new Date().toISOString().slice(0, 10))
const paymentMode = ref<PaymentMode>('Bank Transfer')
const payer = ref('')
const referenceNumber = ref('')
const notes = ref('')
const proofFile = ref<File>()
const proofFileError = ref<string>()

function resetForm(): void {
  amountReceived.value = 0
  paymentDate.value = new Date().toISOString().slice(0, 10)
  paymentMode.value = 'Bank Transfer'
  payer.value = ''
  referenceNumber.value = ''
  notes.value = ''
  proofFile.value = undefined
  proofFileError.value = undefined
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) resetForm()
  },
)

// Which obligation(s) this payment can settle -- just the one the dialog
// was opened against (clicking "Record Payment" on a specific
// installment row) when there is one, otherwise every outstanding
// obligation on this agreement, oldest/earliest due first.
const targetObligations = computed(() =>
  props.preselectedObligationId
    ? props.outstandingObligations.filter((obligation) => obligation.id === props.preselectedObligationId)
    : props.outstandingObligations,
)

const totalOutstanding = computed(
  () => Math.round(targetObligations.value.reduce((sum, obligation) => sum + getObligationAmountPending(obligation), 0) * 100) / 100,
)

// No manual "which obligation(s) does this settle" step any more --
// staff just enter what was received and it's applied automatically,
// oldest obligation first, filling each fully before moving to the next.
const allocations = computed(() => {
  let remaining = amountReceived.value
  const result: { obligationId: string; amount: number }[] = []
  for (const obligation of targetObligations.value) {
    if (remaining <= 0) break
    const amount = Math.round(Math.min(getObligationAmountPending(obligation), remaining) * 100) / 100
    if (amount > 0) result.push({ obligationId: obligation.id, amount })
    remaining = Math.round((remaining - amount) * 100) / 100
  }
  return result
})

// Amount Received can't exceed what's actually outstanding to apply it
// to -- there's nowhere left for the excess to go now that staff can't
// manually redirect it elsewhere.
const exceedsOutstanding = computed(() => amountReceived.value > totalOutstanding.value + 0.009)

const canSubmit = computed(
  () => amountReceived.value > 0 && payer.value.trim().length > 0 && allocations.value.length > 0 && !exceedsOutstanding.value,
)

function handleSubmit(): void {
  if (!canSubmit.value) return
  const input: RecordPaymentInput = {
    agreementId: props.agreementId,
    projectId: props.projectId,
    amountReceived: amountReceived.value,
    paymentDate: paymentDate.value,
    paymentMode: paymentMode.value,
    referenceNumber: referenceNumber.value.trim() || undefined,
    payer: payer.value.trim(),
    notes: notes.value.trim() || undefined,
    allocations: allocations.value,
  }
  emit('submit', input, proofFile.value)
}

function handleClose(): void {
  emit('update:modelValue', false)
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="Record Payment" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-6">
      <FormSection title="Payment Details">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <div class="flex flex-col gap-1">
            <NumberInput
              :model-value="amountReceived"
              label="Amount Received"
              :min="0"
              step="0.01"
              required
              :error="exceedsOutstanding ? `Exceeds the ${formatCurrency(totalOutstanding, currency)} outstanding` : undefined"
              @update:model-value="amountReceived = Number($event)"
            />
            <p class="text-xs text-text-muted">
              Applied automatically to {{ preselectedObligationId ? 'this installment' : 'outstanding installments, oldest due first' }}.
            </p>
          </div>
          <DatePicker v-model="paymentDate" label="Payment Date" required />
          <SelectBox :model-value="paymentMode" label="Payment Mode" :options="PAYMENT_MODE_OPTIONS" @update:model-value="paymentMode = $event as PaymentMode" />
          <TextInput v-model="payer" label="Payer" placeholder="Name of the person/company paying" required />
          <TextInput v-model="referenceNumber" label="Reference Number" placeholder="Transaction/cheque reference" />
        </div>
        <TextArea v-model="notes" label="Notes" :rows="2" />

        <div class="flex flex-col gap-1.5">
          <label class="text-sm font-medium text-text-secondary">Payment Proof (optional)</label>
          <FileUploader
            accept=".pdf,.png,.jpg,.jpeg"
            hint="Receipt, transfer slip, or similar (PDF or image)"
            :allowed-extensions="['.pdf', '.png', '.jpg', '.jpeg']"
            :max-size-bytes="50 * 1024 * 1024"
            @select="proofFile = $event"
            @error="proofFileError = $event"
          />
          <p v-if="proofFileError" class="text-xs text-danger-500">{{ proofFileError }}</p>
        </div>

        <p v-if="targetObligations.length === 0" class="text-sm text-danger-500">
          No outstanding installment{{ preselectedObligationId ? '' : 's' }} to record this payment against.
        </p>
      </FormSection>
    </div>

    <template #footer>
      <FormActionBar submit-label="Record Payment" :loading="isSubmitting" :disabled="!canSubmit" @submit="handleSubmit" @cancel="handleClose" />
    </template>
  </BaseDialog>
</template>
