<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'

import BaseDialog from '@/components/common/BaseDialog.vue'
import Checkbox from '@/components/common/Checkbox.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import FormSection from '@/components/common/FormSection.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { formatCurrency } from '@/utils/currencyFormatter'
import { formatDate } from '@/utils/dateFormatter'
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
const selectedObligationIds = ref<string[]>([])
const allocationAmounts = reactive<Record<string, number>>({})
const proofFile = ref<File>()
const proofFileError = ref<string>()

function resetForm(): void {
  amountReceived.value = 0
  paymentDate.value = new Date().toISOString().slice(0, 10)
  paymentMode.value = 'Bank Transfer'
  payer.value = ''
  referenceNumber.value = ''
  notes.value = ''
  selectedObligationIds.value = props.preselectedObligationId ? [props.preselectedObligationId] : []
  Object.keys(allocationAmounts).forEach((key) => delete allocationAmounts[key])
  proofFile.value = undefined
  proofFileError.value = undefined
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) resetForm()
  },
)

function toggleObligation(obligationId: string, checked: boolean | string | number): void {
  if (checked) {
    if (!selectedObligationIds.value.includes(obligationId)) selectedObligationIds.value.push(obligationId)
  } else {
    selectedObligationIds.value = selectedObligationIds.value.filter((id) => id !== obligationId)
    delete allocationAmounts[obligationId]
  }
}

// Waterfall default: when the received amount or selection changes,
// suggest allocation amounts by filling each selected obligation (in
// schedule order) up to its pending amount before moving to the next.
// The user can still edit any individual amount afterward.
watch([amountReceived, selectedObligationIds], () => {
  let remaining = amountReceived.value
  const orderedSelected = props.outstandingObligations.filter((obligation) => selectedObligationIds.value.includes(obligation.id))

  orderedSelected.forEach((obligation) => {
    const pending = getObligationAmountPending(obligation)
    const suggested = Math.max(0, Math.min(pending, remaining))
    allocationAmounts[obligation.id] = Math.round(suggested * 100) / 100
    remaining = Math.round((remaining - suggested) * 100) / 100
  })
})

const totalAllocated = computed(() =>
  Math.round(selectedObligationIds.value.reduce((sum, id) => sum + (allocationAmounts[id] ?? 0), 0) * 100) / 100,
)

const allocationMismatch = computed(() => Math.abs(totalAllocated.value - amountReceived.value) > 0.009)

// A manual override can otherwise allocate more to one obligation than
// it actually needs (as long as the total still matches amountReceived
// overall) -- caught here per-row, mirroring the same cap the backend
// now enforces in payment_service.record_payment.
const overAllocatedObligationIds = computed(() =>
  new Set(
    props.outstandingObligations
      .filter((obligation) => selectedObligationIds.value.includes(obligation.id))
      .filter((obligation) => (allocationAmounts[obligation.id] ?? 0) > getObligationAmountPending(obligation) + 0.009)
      .map((obligation) => obligation.id),
  ),
)

const canSubmit = computed(
  () =>
    amountReceived.value > 0 &&
    payer.value.trim().length > 0 &&
    selectedObligationIds.value.length > 0 &&
    !allocationMismatch.value &&
    overAllocatedObligationIds.value.size === 0,
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
    allocations: selectedObligationIds.value.map((obligationId) => ({ obligationId, amount: allocationAmounts[obligationId] ?? 0 })),
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
          <NumberInput :model-value="amountReceived" label="Amount Received" :min="0" step="0.01" required @update:model-value="amountReceived = Number($event)" />
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
      </FormSection>

      <FormSection title="Allocation" description="Select which payment obligation(s) this payment settles.">
        <div v-if="outstandingObligations.length === 0" class="text-sm text-text-muted">No outstanding obligations to allocate against.</div>
        <div v-for="obligation in outstandingObligations" :key="obligation.id" class="rounded-lg border border-border-light p-3">
          <div class="flex items-center justify-between gap-3">
            <Checkbox
              :model-value="selectedObligationIds.includes(obligation.id)"
              :label="`${obligation.description} — due ${formatDate(obligation.dueDate)}`"
              :hint="`Pending: ${formatCurrency(getObligationAmountPending(obligation), currency)}`"
              @update:model-value="toggleObligation(obligation.id, $event)"
            />
            <NumberInput
              v-if="selectedObligationIds.includes(obligation.id)"
              :model-value="allocationAmounts[obligation.id] ?? 0"
              :min="0"
              :max="getObligationAmountPending(obligation)"
              step="0.01"
              class="w-32"
              :error="overAllocatedObligationIds.has(obligation.id) ? `Exceeds pending (${formatCurrency(getObligationAmountPending(obligation), currency)})` : undefined"
              @update:model-value="allocationAmounts[obligation.id] = Number($event)"
            />
          </div>
        </div>
        <p class="text-xs" :class="allocationMismatch ? 'font-medium text-danger-500' : 'text-text-muted'">
          Allocated {{ formatCurrency(totalAllocated, currency) }} of {{ formatCurrency(amountReceived, currency) }} received
        </p>
      </FormSection>
    </div>

    <template #footer>
      <FormActionBar submit-label="Record Payment" :loading="isSubmitting" :disabled="!canSubmit" @submit="handleSubmit" @cancel="handleClose" />
    </template>
  </BaseDialog>
</template>
