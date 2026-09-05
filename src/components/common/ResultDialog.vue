<script setup lang="ts">
import { CheckCircle2, XCircle } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import { useResultDialogStore } from '@/stores/resultDialogStore'

const store = useResultDialogStore()
const { t } = useI18n()

const icon = computed(() => (store.status === 'success' ? CheckCircle2 : XCircle))
const iconClass = computed(() => (store.status === 'success' ? 'text-success-500' : 'text-danger-500'))
</script>

<template>
  <BaseDialog :model-value="store.isOpen" size="sm" :closable="false" @update:model-value="store.close">
    <div class="flex flex-col items-center gap-3 py-2 text-center">
      <component :is="icon" class="h-12 w-12 shrink-0" :class="iconClass" />
      <h2 class="text-lg font-semibold text-text-primary">{{ store.title }}</h2>
      <p v-if="store.description" class="text-sm text-text-secondary">{{ store.description }}</p>
    </div>

    <template #footer>
      <BaseButton class="w-full" @click="store.close">{{ t('common.ok') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
