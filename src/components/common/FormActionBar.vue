<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { ButtonVariant } from '@/types/Ui'
import BaseButton from './BaseButton.vue'

interface Props {
  submitLabel?: string
  submitVariant?: ButtonVariant
  cancelLabel?: string
  loading?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  submitLabel: undefined,
  submitVariant: 'primary',
  cancelLabel: undefined,
  loading: false,
  disabled: false,
})

const { t } = useI18n()

defineEmits<{
  submit: []
  cancel: []
}>()
</script>

<template>
  <div class="flex items-center justify-end gap-3 border-t border-border-light pt-4">
    <BaseButton variant="ghost" :disabled="disabled || loading" @click="$emit('cancel')">
      {{ props.cancelLabel ?? t('common.cancel') }}
    </BaseButton>
    <BaseButton
      :variant="submitVariant"
      :disabled="disabled || loading"
      :loading="loading"
      @click="$emit('submit')"
    >
      {{ props.submitLabel ?? t('common.save') }}
    </BaseButton>
  </div>
</template>
