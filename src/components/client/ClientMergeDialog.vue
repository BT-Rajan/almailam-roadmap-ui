<script setup lang="ts">
import { ArrowLeftRight } from '@lucide/vue'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { Client, ClientDuplicateMatch } from '@/types/Client'
import { getClientDisplayName, getClientOnboardingStateVariant } from '@/utils/clientHelpers'
import { formatDate } from '@/utils/dateFormatter'

const props = defineProps<{
  modelValue: boolean
  currentClient: Client
  match: ClientDuplicateMatch | null
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  /** direction: which client's data is kept as the surviving record. */
  confirm: [direction: 'keep-current' | 'keep-other']
}>()

const { t } = useI18n()

// Defaults to keeping whichever record is further along (Ready beats
// anything else), since that's usually the more complete, more trusted
// record -- but either direction is always available.
const direction = ref<'keep-current' | 'keep-other'>('keep-current')

watch(
  () => props.modelValue,
  (open) => {
    if (!open || !props.match) return
    const currentIsFurtherAlong = props.currentClient.onboardingState === 'Ready' || props.match.client.onboardingState !== 'Ready'
    direction.value = currentIsFurtherAlong ? 'keep-current' : 'keep-other'
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

// Completes the WAI-ARIA radiogroup pattern: arrow keys move the
// selection, not just a mouse click -- with exactly two mutually
// exclusive options, any arrow key simply flips between them.
function toggleDirection(): void {
  direction.value = direction.value === 'keep-current' ? 'keep-other' : 'keep-current'
}

function handleOptionKeydown(event: KeyboardEvent): void {
  if (['ArrowRight', 'ArrowLeft', 'ArrowUp', 'ArrowDown'].includes(event.key)) {
    event.preventDefault()
    toggleDirection()
  }
}
</script>

<template>
  <BaseDialog v-if="match" :model-value="modelValue" :title="t('client.mergeDialog.title')" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <p class="text-sm text-text-secondary">
        {{ t('client.mergeDialog.description', { fields: match.matchedOn.join(', ') }) }}
      </p>

      <div class="grid grid-cols-1 gap-3 tablet:grid-cols-2" role="radiogroup" :aria-label="t('client.mergeDialog.whichRecordToKeep')">
        <button
          type="button"
          role="radio"
          :aria-checked="direction === 'keep-current'"
          class="flex flex-col gap-2 rounded-lg border p-4 text-left transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500"
          :class="direction === 'keep-current' ? 'border-primary-500 bg-primary-50' : 'border-border-light hover:border-primary-300'"
          @click="direction = 'keep-current'"
          @keydown="handleOptionKeydown"
        >
          <span class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('client.mergeDialog.keepThisRecord') }}</span>
          <span class="text-sm font-semibold text-text-primary">{{ getClientDisplayName(currentClient) }}</span>
          <span class="text-xs text-text-muted">{{ currentClient.code }} · {{ t('client.mergeDialog.createdOn', { date: formatDate(currentClient.createdDate) }) }}</span>
          <StatusBadge :label="currentClient.onboardingState" :variant="getClientOnboardingStateVariant(currentClient.onboardingState)" size="sm" />
        </button>

        <button
          type="button"
          role="radio"
          :aria-checked="direction === 'keep-other'"
          class="flex flex-col gap-2 rounded-lg border p-4 text-left transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500"
          :class="direction === 'keep-other' ? 'border-primary-500 bg-primary-50' : 'border-border-light hover:border-primary-300'"
          @click="direction = 'keep-other'"
          @keydown="handleOptionKeydown"
        >
          <span class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ t('client.mergeDialog.keepOtherRecord') }}</span>
          <span class="text-sm font-semibold text-text-primary">{{ getClientDisplayName(match.client) }}</span>
          <span class="text-xs text-text-muted">{{ match.client.code }} · {{ t('client.mergeDialog.createdOn', { date: formatDate(match.client.createdDate) }) }}</span>
          <StatusBadge :label="match.client.onboardingState" :variant="getClientOnboardingStateVariant(match.client.onboardingState)" size="sm" />
        </button>
      </div>

      <p class="text-xs text-text-muted">{{ t('client.mergeDialog.cannotBeUndone') }}</p>
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">{{ t('common.cancel') }}</BaseButton>
      <BaseButton variant="danger" :icon="ArrowLeftRight" :loading="loading" @click="emit('confirm', direction)">
        {{ t('client.mergeDialog.mergeClients') }}
      </BaseButton>
    </template>
  </BaseDialog>
</template>
