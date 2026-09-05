<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import TextArea from '@/components/common/TextArea.vue'
import type { PaymentObligation } from '@/types/Payment'

interface Props {
  modelValue: boolean
  mode: 'cancel' | 'waive'
  obligation: PaymentObligation | undefined
  isSubmitting?: boolean
}

const props = withDefaults(defineProps<Props>(), { isSubmitting: false })

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [reason: string]
}>()

const { t } = useI18n()

const reason = ref('')

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) reason.value = ''
  },
)

const title = computed(() => (props.mode === 'cancel' ? t('payment.obligationActionDialog.cancelTitle') : t('payment.obligationActionDialog.waiveTitle')))
const canConfirm = computed(() => reason.value.trim().length > 0)

function handleCancel(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  if (!canConfirm.value) return
  emit('confirm', reason.value.trim())
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="title" size="sm" @update:model-value="emit('update:modelValue', $event)" @close="handleCancel">
    <p class="text-sm text-text-secondary">
      {{ mode === 'cancel' ? t('payment.obligationActionDialog.cancellingText') : t('payment.obligationActionDialog.waivingText') }} "{{ obligation?.description }}" {{ t('payment.obligationActionDialog.consequenceText') }}
    </p>
    <TextArea v-model="reason" :label="t('payment.obligationActionDialog.reason')" class="mt-4" :rows="3" required />

    <template #footer>
      <BaseButton variant="secondary" :disabled="isSubmitting" @click="handleCancel">{{ t('payment.obligationActionDialog.back') }}</BaseButton>
      <BaseButton variant="danger" :loading="isSubmitting" :disabled="!canConfirm" @click="handleConfirm">
        {{ mode === 'cancel' ? t('payment.obligationActionDialog.confirmCancellation') : t('payment.obligationActionDialog.confirmWaiver') }}
      </BaseButton>
    </template>
  </BaseDialog>
</template>
