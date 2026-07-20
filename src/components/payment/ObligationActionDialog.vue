<script setup lang="ts">
import { computed, ref, watch } from 'vue'

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

const reason = ref('')

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) reason.value = ''
  },
)

const title = computed(() => (props.mode === 'cancel' ? 'Cancel Payment Obligation' : 'Waive Payment Obligation'))
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
    <p class="text-sm text-neutral-600">
      {{ mode === 'cancel' ? 'Cancelling' : 'Waiving' }} "{{ obligation?.description }}" removes it from pending/overdue totals. This action is logged and cannot be silently undone.
    </p>
    <TextArea v-model="reason" label="Reason" class="mt-4" :rows="3" required />

    <template #footer>
      <BaseButton variant="secondary" :disabled="isSubmitting" @click="handleCancel">Back</BaseButton>
      <BaseButton variant="danger" :loading="isSubmitting" :disabled="!canConfirm" @click="handleConfirm">
        {{ mode === 'cancel' ? 'Confirm Cancellation' : 'Confirm Waiver' }}
      </BaseButton>
    </template>
  </BaseDialog>
</template>
