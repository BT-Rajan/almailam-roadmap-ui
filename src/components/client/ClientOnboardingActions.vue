<script setup lang="ts">
import { ArrowRight, Settings2 } from '@lucide/vue'
import { computed } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { CLIENT_ONBOARDING_ALLOWED_TRANSITIONS } from '@/constants/clientOptions'
import type { Client, ClientAddress, ClientContact, ClientDocument, ClientOnboardingState, ClientVerification } from '@/types/Client'
import { calculateOnboardingState, getClientOnboardingStateVariant } from '@/utils/clientHelpers'

const props = defineProps<{
  client: Client
  documents: ClientDocument[]
  contacts: ClientContact[]
  addresses: ClientAddress[]
  verifications: ClientVerification[]
  loading?: boolean
}>()

const emit = defineEmits<{
  advance: [nextState: ClientOnboardingState]
  changeStatus: []
}>()

// What the actual contacts/addresses/documents/verifications on file say
// the state should be -- calculated fresh from real data rather than
// trusted from whatever onboardingState happens to be stored (see
// utils/clientHelpers).
const recommendedState = computed(() =>
  calculateOnboardingState(props.client, props.documents, props.contacts, props.addresses, props.verifications),
)

const availableTransitions = computed(
  () => CLIENT_ONBOARDING_ALLOWED_TRANSITIONS[props.client.onboardingState] ?? [],
)

// Only offer the one-click "Advance" shortcut when the recommended state
// is both different from the current one and a transition the backend's
// state machine actually allows from here -- otherwise it falls through
// to the manual "Change Status" dialog instead.
const canAutoAdvance = computed(
  () =>
    recommendedState.value !== props.client.onboardingState &&
    availableTransitions.value.includes(recommendedState.value),
)
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-neutral-800">Onboarding Status</h3>
    </template>

    <div class="flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <span class="text-sm text-neutral-500">Current status</span>
        <StatusBadge :label="client.onboardingState" :variant="getClientOnboardingStateVariant(client.onboardingState)" />
      </div>

      <p v-if="canAutoAdvance" class="text-xs text-neutral-500">
        Based on the documents and verifications on file, this client is ready to move to
        <strong>{{ recommendedState }}</strong>.
      </p>
      <p v-else-if="availableTransitions.length === 0" class="text-xs text-neutral-400">
        No further status changes are available from this status.
      </p>

      <div class="flex flex-wrap items-center gap-2">
        <BaseButton
          v-if="canAutoAdvance"
          size="sm"
          :icon="ArrowRight"
          :loading="loading"
          @click="emit('advance', recommendedState)"
        >
          Advance to {{ recommendedState }}
        </BaseButton>
        <BaseButton
          v-if="availableTransitions.length > 0"
          variant="secondary"
          size="sm"
          :icon="Settings2"
          :disabled="loading"
          @click="emit('changeStatus')"
        >
          Change Status
        </BaseButton>
      </div>
    </div>
  </Card>
</template>
