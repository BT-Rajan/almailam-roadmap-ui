<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseDialog from '@/components/common/BaseDialog.vue'
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

const { t } = useI18n()

const ADJUSTMENT_TYPE_OPTIONS: SelectOption[] = [
  { label: 'Increase', value: 'Increase', labelKey: 'payment.financialActionDialog.adjustmentTypeIncrease' },
  { label: 'Decrease', value: 'Decrease', labelKey: 'payment.financialActionDialog.adjustmentTypeDecrease' },
  { label: 'Correction', value: 'Correction', labelKey: 'payment.financialActionDialog.adjustmentTypeCorrection' },
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
  <BaseDialog :model-value="modelValue" :title="mode === 'refund' ? t('payment.financialActionDialog.issueRefundTitle') : t('payment.financialActionDialog.adjustObligationTitle')" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <FormSection :description="mode === 'refund' ? t('payment.financialActionDialog.refundDescription') : t('payment.financialActionDialog.adjustmentDescription')">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <SelectBox :model-value="obligationId" :label="t('payment.financialActionDialog.obligation')" :options="obligationOptions" @update:model-value="obligationId = String($event)" />
        <SelectBox v-if="mode === 'adjustment'" :model-value="adjustmentType" :label="t('payment.financialActionDialog.adjustmentType')" :options="ADJUSTMENT_TYPE_OPTIONS" @update:model-value="adjustmentType = $event as AdjustmentType" />
        <NumberInput :model-value="amount" :label="mode === 'refund' ? t('payment.financialActionDialog.refundAmount') : t('payment.financialActionDialog.amount')" :min="0" step="0.01" required @update:model-value="amount = Number($event)" />
        <DatePicker v-if="mode === 'refund'" v-model="actionDate" :label="t('payment.financialActionDialog.refundDate')" required />
        <TextInput v-if="mode === 'refund'" v-model="reference" :label="t('payment.financialActionDialog.referenceOptional')" placeholder="RFD-…" />
        <TextInput v-model="authorisingUser" :label="t('payment.financialActionDialog.authorisingUser')" required />
      </div>
      <TextArea v-model="reason" :label="t('payment.financialActionDialog.reason')" :rows="3" required />
    </FormSection>

    <template #footer>
      <FormActionBar :submit-label="mode === 'refund' ? t('payment.financialActionDialog.issueRefund') : t('payment.financialActionDialog.applyAdjustment')" :loading="isSubmitting" :disabled="!canSubmit" @submit="handleSubmit" @cancel="handleClose" />
    </template>
  </BaseDialog>
</template>
