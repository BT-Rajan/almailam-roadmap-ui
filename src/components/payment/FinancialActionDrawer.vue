<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import BaseDrawer from '@/components/common/BaseDrawer.vue'
import DatePicker from '@/components/common/DatePicker.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import FormSection from '@/components/common/FormSection.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { formatCurrency } from '@/utils/currencyFormatter'
import type { AdjustmentType, PaymentObligation } from '@/types/Payment'
import type { SelectOption } from '@/types/Ui'

interface Props {
  modelValue: boolean
  mode: 'refund' | 'adjustment'
  obligations: PaymentObligation[]
  currency: string
  isSubmitting?: boolean
}

const props = withDefaults(defineProps<Props>(), { isSubmitting: false })

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  submitRefund: [input: { obligationId: string; refundAmount: number; refundDate: string; reason: string; authorisingUser: string; reference?: string }]
  submitAdjustment: [input: { obligationId: string; type: AdjustmentType; amount: number; reason: string; authorisingUser: string }]
}>()

const ADJUSTMENT_TYPE_OPTIONS: SelectOption[] = [
  { label: 'Increase', value: 'Increase' },
  { label: 'Decrease', value: 'Decrease' },
  { label: 'Correction', value: 'Correction' },
]

const obligationId = ref('')
const amount = ref(0)
const actionDate = ref(new Date().toISOString().slice(0, 10))
const reason = ref('')
const authorisingUser = ref('Rajan Kumar')
const reference = ref('')
const adjustmentType = ref<AdjustmentType>('Increase')

const obligationOptions = computed<SelectOption[]>(() =>
  props.obligations.map((obligation) => ({ label: `${obligation.description} (${formatCurrency(obligation.amountDue, props.currency)})`, value: obligation.id })),
)

function resetForm(): void {
  obligationId.value = props.obligations[0]?.id ?? ''
  amount.value = 0
  actionDate.value = new Date().toISOString().slice(0, 10)
  reason.value = ''
  authorisingUser.value = 'Rajan Kumar'
  reference.value = ''
  adjustmentType.value = 'Increase'
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) resetForm()
  },
)

const canSubmit = computed(() => obligationId.value.length > 0 && amount.value > 0 && reason.value.trim().length > 0 && authorisingUser.value.trim().length > 0)

function handleSubmit(): void {
  if (!canSubmit.value) return
  if (props.mode === 'refund') {
    emit('submitRefund', {
      obligationId: obligationId.value,
      refundAmount: amount.value,
      refundDate: actionDate.value,
      reason: reason.value.trim(),
      authorisingUser: authorisingUser.value.trim(),
      reference: reference.value.trim() || undefined,
    })
  } else {
    emit('submitAdjustment', {
      obligationId: obligationId.value,
      type: adjustmentType.value,
      amount: amount.value,
      reason: reason.value.trim(),
      authorisingUser: authorisingUser.value.trim(),
    })
  }
}

function handleClose(): void {
  emit('update:modelValue', false)
}
</script>

<template>
  <BaseDrawer :model-value="modelValue" :title="mode === 'refund' ? 'Issue Refund' : 'Adjust Obligation'" width="md" @update:model-value="emit('update:modelValue', $event)">
    <FormSection :description="mode === 'refund' ? 'Refunds are recorded against the original payment record — the payment itself is never altered.' : 'Adjustments require a reason and are fully auditable.'">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <SelectBox :model-value="obligationId" label="Obligation" :options="obligationOptions" @update:model-value="obligationId = String($event)" />
        <SelectBox v-if="mode === 'adjustment'" :model-value="adjustmentType" label="Adjustment Type" :options="ADJUSTMENT_TYPE_OPTIONS" @update:model-value="adjustmentType = $event as AdjustmentType" />
        <NumberInput :model-value="amount" :label="mode === 'refund' ? 'Refund Amount' : 'Amount'" :min="0" step="0.01" required @update:model-value="amount = Number($event)" />
        <DatePicker v-if="mode === 'refund'" v-model="actionDate" label="Refund Date" required />
        <TextInput v-if="mode === 'refund'" v-model="reference" label="Reference (optional)" placeholder="RFD-…" />
        <TextInput v-model="authorisingUser" label="Authorising User" required />
      </div>
      <TextArea v-model="reason" label="Reason" :rows="3" required />
    </FormSection>

    <template #footer>
      <FormActionBar :submit-label="mode === 'refund' ? 'Issue Refund' : 'Apply Adjustment'" :loading="isSubmitting" :disabled="!canSubmit" @submit="handleSubmit" @cancel="handleClose" />
    </template>
  </BaseDrawer>
</template>
