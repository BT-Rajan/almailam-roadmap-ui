<script setup lang="ts">
import { useI18n } from 'vue-i18n'

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

const props = withDefaults(defineProps<Props>(), {
  confirmLabel: undefined,
  cancelLabel: undefined,
  confirmVariant: 'primary',
  loading: false,
})

const { t } = useI18n()

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
    <p class="text-sm text-text-secondary">{{ message }}</p>

    <template #footer>
      <BaseButton variant="secondary" :disabled="loading" @click="handleCancel">
        {{ props.cancelLabel ?? t('common.cancel') }}
      </BaseButton>
      <BaseButton :variant="confirmVariant" :loading="loading" @click="$emit('confirm')">
        {{ props.confirmLabel ?? t('common.confirm') }}
      </BaseButton>
    </template>
  </BaseDialog>
</template>
