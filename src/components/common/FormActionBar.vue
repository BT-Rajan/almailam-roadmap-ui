<script setup lang="ts">
import type { ButtonVariant } from '@/types/Ui'
import BaseButton from './BaseButton.vue'

interface Props {
  submitLabel?: string
  submitVariant?: ButtonVariant
  cancelLabel?: string
  loading?: boolean
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  submitLabel: 'Save',
  submitVariant: 'primary',
  cancelLabel: 'Cancel',
  loading: false,
  disabled: false,
})

defineEmits<{
  submit: []
  cancel: []
}>()
</script>

<template>
  <div class="flex items-center justify-end gap-3 border-t border-border-light pt-4">
    <BaseButton variant="ghost" :disabled="disabled || loading" @click="$emit('cancel')">
      {{ cancelLabel }}
    </BaseButton>
    <BaseButton
      :variant="submitVariant"
      :disabled="disabled || loading"
      :loading="loading"
      @click="$emit('submit')"
    >
      {{ submitLabel }}
    </BaseButton>
  </div>
</template>
