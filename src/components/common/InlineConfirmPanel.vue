<script setup lang="ts">
import { AlertTriangle } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'

// An in-page confirmation for a destructive action -- shown where the
// action was started instead of in a modal, same "stay on the page"
// idea as the New Quotation/Contract/Permit Application pages.
interface Props {
  title: string
  message: string
  confirmLabel: string
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  loading: false,
})

defineEmits<{
  confirm: []
  cancel: []
}>()

const { t } = useI18n()
</script>

<template>
  <div class="flex flex-col gap-3 rounded-lg border border-danger-100 bg-danger-50 p-4 text-danger-700 tablet:flex-row tablet:items-center tablet:justify-between" role="alertdialog" :aria-label="title">
    <div class="flex items-start gap-3">
      <AlertTriangle class="mt-0.5 h-5 w-5 shrink-0" />
      <div>
        <p class="text-sm font-semibold">{{ title }}</p>
        <p class="mt-0.5 text-sm opacity-90">{{ message }}</p>
      </div>
    </div>
    <div class="flex shrink-0 items-center gap-2 no-print">
      <BaseButton variant="secondary" size="sm" :disabled="loading" @click="$emit('cancel')">{{ t('common.cancel') }}</BaseButton>
      <BaseButton variant="danger" size="sm" :loading="loading" @click="$emit('confirm')">{{ confirmLabel }}</BaseButton>
    </div>
  </div>
</template>
