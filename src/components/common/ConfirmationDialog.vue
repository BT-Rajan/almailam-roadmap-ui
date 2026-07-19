<script setup lang="ts">
import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import type { ButtonVariant } from '@/types/Ui'

interface Props {
  modelValue: boolean
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  confirmVariant?: ButtonVariant
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  confirmLabel: 'Confirm',
  cancelLabel: 'Cancel',
  confirmVariant: 'primary',
  loading: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: []
  cancel: []
}>()

const handleCancel = (): void => {
  emit('update:modelValue', false)
  emit('cancel')
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="title"
    size="sm"
    @update:model-value="emit('update:modelValue', $event)"
    @close="handleCancel"
  >
    <p class="text-sm text-neutral-600">{{ message }}</p>

    <template #footer>
      <BaseButton variant="secondary" :disabled="loading" @click="handleCancel">
        {{ cancelLabel }}
      </BaseButton>
      <BaseButton :variant="confirmVariant" :loading="loading" @click="$emit('confirm')">
        {{ confirmLabel }}
      </BaseButton>
    </template>
  </BaseDialog>
</template>
