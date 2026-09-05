<script setup lang="ts">
import { Mail, MapPin, Phone, UserRound } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { Client } from '@/types/Client'
import { getClientDisplayName, getClientOnboardingStateVariant, getClientStatusVariant } from '@/utils/clientHelpers'

const props = defineProps<{
  client: Client
}>()

const { t } = useI18n()

const displayName = computed(() => getClientDisplayName(props.client))

const CLIENT_TYPE_LABEL_KEYS: Record<string, string> = {
  Individual: 'clientOptions.type.individual',
  Company: 'clientOptions.type.company',
  Organisation: 'clientOptions.type.organisation',
  'Government Entity': 'clientOptions.type.governmentEntity',
  Other: 'clientOptions.type.other',
}
const clientTypeLabel = computed(() => t(CLIENT_TYPE_LABEL_KEYS[props.client.clientType] ?? props.client.clientType))

const CLIENT_STATUS_LABEL_KEYS: Record<string, string> = {
  Active: 'clientOptions.status.active',
  Inactive: 'clientOptions.status.inactive',
}
const clientStatusLabel = computed(() => t(CLIENT_STATUS_LABEL_KEYS[props.client.status] ?? props.client.status))

const ONBOARDING_STATE_LABEL_KEYS: Record<string, string> = {
  'Information Required': 'clientOptions.onboardingState.informationRequired',
  'Documents Required': 'clientOptions.onboardingState.documentsRequired',
  'Under Review': 'clientOptions.onboardingState.underReview',
  Ready: 'clientOptions.onboardingState.ready',
  Rejected: 'clientOptions.onboardingState.rejected',
  Suspended: 'clientOptions.onboardingState.suspended',
}
const onboardingStateLabel = computed(() => t(ONBOARDING_STATE_LABEL_KEYS[props.client.onboardingState] ?? props.client.onboardingState))

const emit = defineEmits<{
  open: [clientId: string]
}>()

function open(): void {
  emit('open', props.client.id)
}

function handleKeydown(event: KeyboardEvent): void {
  // The whole card acts as one big button -- Enter and Space both
  // activate it, matching how a native <button> behaves, since a
  // mouse-only @click here would otherwise make every client in the
  // grid unreachable to keyboard and screen-reader users entirely.
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    open()
  }
}
</script>

<template>
  <Card
    hoverable
    class="cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500"
    role="button"
    tabindex="0"
    :aria-label="t('client.card.openClient', { name: displayName })"
    @click="open"
    @keydown="handleKeydown"
  >
    <div class="flex flex-col gap-4">
      <div class="flex items-start justify-between gap-3">
        <div class="flex flex-col gap-1">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ client.code }} · {{ clientTypeLabel }}</p>
          <h3 class="text-base font-semibold leading-snug text-text-primary">{{ displayName }}</h3>
        </div>
        <StatusBadge :label="clientStatusLabel" :variant="getClientStatusVariant(client.status)" show-dot />
      </div>

      <div class="flex flex-col gap-1.5 text-sm text-text-muted">
        <div class="flex items-center gap-2">
          <Phone class="h-4 w-4 shrink-0 text-text-muted" />
          <span class="truncate">{{ client.mobile }}</span>
        </div>
        <div class="flex items-center gap-2">
          <Mail class="h-4 w-4 shrink-0 text-text-muted" />
          <span class="truncate">{{ client.email }}</span>
        </div>
        <div class="flex items-center gap-2">
          <MapPin class="h-4 w-4 shrink-0 text-text-muted" />
          <span class="truncate">{{ client.city }}</span>
        </div>
        <div class="flex items-center gap-2">
          <UserRound class="h-4 w-4 shrink-0 text-text-muted" />
          <span class="truncate">{{ client.accountManagerName ?? t('client.unassigned') }}</span>
        </div>
      </div>

      <div class="flex items-center justify-between border-t border-border-light pt-3">
        <StatusBadge :label="onboardingStateLabel" :variant="getClientOnboardingStateVariant(client.onboardingState)" size="sm" />
      </div>
    </div>
  </Card>
</template>
