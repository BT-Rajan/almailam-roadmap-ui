<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import Alert from '@/components/common/Alert.vue'
import type { ClientDuplicateMatch } from '@/types/Client'
import { getClientDisplayName } from '@/utils/clientHelpers'

defineProps<{
  matches: ClientDuplicateMatch[]
}>()

defineEmits<{
  view: [clientId: string]
}>()

const { t } = useI18n()
</script>

<template>
  <div v-if="matches.length > 0" class="flex flex-col gap-2">
    <Alert
      variant="warning"
      :title="t('client.duplicateAlert.title')"
      :description="t('client.duplicateAlert.description')"
    />
    <ul class="flex flex-col gap-2">
      <li
        v-for="match in matches"
        :key="match.client.id"
        class="flex items-center justify-between gap-3 rounded-lg border border-warning-100 bg-warning-50 px-4 py-2.5"
      >
        <div class="flex flex-col">
          <span class="text-sm font-medium text-text-primary">{{ getClientDisplayName(match.client) }}</span>
          <span class="text-xs text-text-muted">{{ t('client.duplicateAlert.matchedOn', { fields: match.matchedOn.join(', '), code: match.client.code }) }}</span>
        </div>
        <button
          type="button"
          :aria-label="t('client.duplicateAlert.viewProfileFor', { name: getClientDisplayName(match.client) })"
          class="rounded text-xs font-medium text-primary-600 hover:text-primary-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500"
          @click="$emit('view', match.client.id)"
        >
          {{ t('client.duplicateAlert.viewProfile') }}
        </button>
      </li>
    </ul>
  </div>
</template>
