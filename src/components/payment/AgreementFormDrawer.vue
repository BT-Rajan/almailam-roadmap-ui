<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import BaseDrawer from '@/components/common/BaseDrawer.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import FormSection from '@/components/common/FormSection.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import type { CreateAgreementInput, PaymentFrequency, PaymentMode } from '@/types/Payment'
import type { SelectOption } from '@/types/Ui'

interface Props {
  modelValue: boolean
  projectId: string
  isSubmitting?: boolean
}

const props = withDefaults(defineProps<Props>(), { isSubmitting: false })

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

const PAYMENT_FREQUENCY_OPTIONS: SelectOption[] = [
  { label: 'One-time', value: 'One-time' },
  { label: 'Monthly', value: 'Monthly' },
  { label: 'Quarterly', value: 'Quarterly' },
  { label: 'Half-yearly', value: 'Half-yearly' },
  { label: 'Yearly', value: 'Yearly' },
  { label: 'Custom', value: 'Custom' },
]

const contractAmount = ref(0)
const currency = ref('KWD')
const contractStartDate = ref(new Date().toISOString().slice(0, 10))
const contractEndDate = ref('')
const agreementDate = ref(new Date().toISOString().slice(0, 10))
const quotationReference = ref('')
const contractReference = ref('')
const paymentMode = ref<PaymentMode>('Bank Transfer')
const paymentFrequency = ref<PaymentFrequency>('Monthly')

const needsEndDate = computed(() => paymentFrequency.value !== 'One-time')

function resetForm(): void {
  contractAmount.value = 0
  currency.value = 'KWD'
  contractStartDate.value = new Date().toISOString().slice(0, 10)
  contractEndDate.value = ''
  agreementDate.value = new Date().toISOString().slice(0, 10)
  quotationReference.value = ''
  contractReference.value = ''
  paymentMode.value = 'Bank Transfer'
  paymentFrequency.value = 'Monthly'
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) resetForm()
  },
)

const canSubmit = computed(() => contractAmount.value > 0 && contractStartDate.value.length > 0 && (!needsEndDate.value || contractEndDate.value.length > 0))

function handleSubmit(): void {
  if (!canSubmit.value) return
  const input: CreateAgreementInput = {
    projectId: props.projectId,
    contractAmount: contractAmount.value,
    currency: currency.value,
    contractStartDate: contractStartDate.value,
    contractEndDate: needsEndDate.value ? contractEndDate.value : undefined,
    agreementDate: agreementDate.value,
    quotationReference: quotationReference.value.trim() || undefined,
    contractReference: contractReference.value.trim() || undefined,
    paymentMode: paymentMode.value,
    paymentFrequency: paymentFrequency.value,
  }
  emit('submit', input)
}

function handleClose(): void {
  emit('update:modelValue', false)
}
</script>

<template>
  <BaseDrawer :model-value="modelValue" title="Create Financial Agreement" width="md" @update:model-value="emit('update:modelValue', $event)">
    <FormSection title="Contract Value" description="The total agreed value of the engagement with this client.">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <NumberInput :model-value="contractAmount" label="Total Contract Amount" :min="0" step="0.01" required @update:model-value="contractAmount = Number($event)" />
        <TextInput v-model="currency" label="Currency" placeholder="KWD" required />
        <DatePicker v-model="agreementDate" label="Agreement Date" required />
        <DatePicker v-model="contractStartDate" label="Contract Start Date" required />
        <DatePicker v-if="needsEndDate" v-model="contractEndDate" label="Contract End Date" required hint="Used to generate the payment schedule." />
        <TextInput v-model="quotationReference" label="Quotation Reference (optional)" placeholder="QTN-2026-…" />
        <TextInput v-model="contractReference" label="Contract Reference (optional)" placeholder="CNT-2026-…" />
      </div>
    </FormSection>

    <FormSection title="Payment Terms" description="A payment schedule will be generated automatically based on the frequency selected.">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <SelectBox :model-value="paymentMode" label="Payment Mode" :options="PAYMENT_MODE_OPTIONS" @update:model-value="paymentMode = $event as PaymentMode" />
        <SelectBox :model-value="paymentFrequency" label="Payment Frequency" :options="PAYMENT_FREQUENCY_OPTIONS" @update:model-value="paymentFrequency = $event as PaymentFrequency" />
      </div>
      <p v-if="paymentFrequency === 'Custom'" class="text-xs text-neutral-500">
        A single obligation for the full amount will be created — add or split individual installments afterward from the payment timeline.
      </p>
    </FormSection>

    <template #footer>
      <FormActionBar submit-label="Create Agreement" :loading="isSubmitting" :disabled="!canSubmit" @submit="handleSubmit" @cancel="handleClose" />
    </template>
  </BaseDrawer>
</template>
