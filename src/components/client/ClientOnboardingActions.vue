<script setup lang="ts">
import { ArrowRightCircle, Settings2 } from '@lucide/vue'
import { computed } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { CLIENT_ONBOARDING_ALLOWED_TRANSITIONS, CLIENT_ONBOARDING_STATES_REQUIRING_REASON } from '@/constants/clientOptions'
import type { Client, ClientAddress, ClientContact, ClientDocument, ClientIdentification, ClientVerification } from '@/types/Client'
import { calculateOnboardingState, getClientOnboardingStateVariant } from '@/utils/clientHelpers'

const props = defineProps<{
  client: Client
  documents: ClientDocument[]
  contacts: ClientContact[]
  addresses: ClientAddress[]
  identifications: ClientIdentification[]
  verifications: ClientVerification[]
  loading?: boolean
}>()

const emit = defineEmits<{
  autoAdvance: []
  changeStatus: []
}>()

// Purely informational -- what the actual contacts/addresses/documents/
// identifications on file say the state should ultimately be, shown as
// context alongside the buttons below. Doesn't drive which button
// appears: the backend doesn't gate transitions on data completeness
// (staff can already manually force any individual step regardless of
// what's on file via "Change Status"), so this is a helpful signal, not
// a precondition.
const recommendedState = computed(() =>
  calculateOnboardingState(
    props.client,
    props.documents,
    props.contacts,
    props.addresses,
    props.identifications,
    props.verifications,
  ),
)

const availableTransitions = computed(
  () => CLIENT_ONBOARDING_ALLOWED_TRANSITIONS[props.client.onboardingState] ?? [],
)

// The bulk "Advance" action only makes sense when the current step has
// exactly one legal next state (nothing to decide) *and* that step
// doesn't require a reason (which needs a human to type one in) --
// backend/app/services/client_service.py's auto_advance_onboarding()
// walks as many such steps as it can in one call, so this button covers
// what used to be several separate "Change Status" round trips for the
// common, no-real-decision case. Anything else -- a branch point, a
// dead end, or a reason-gated step -- falls through to "Change Status".
const canAutoAdvance = computed(
  () => availableTransitions.value.length === 1 && !CLIENT_ONBOARDING_STATES_REQUIRING_REASON.includes(availableTransitions.value[0]),
)
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">Onboarding Status</h3>
    </template>

    <div class="flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <span class="text-sm text-text-muted">Current status</span>
        <StatusBadge :label="client.onboardingState" :variant="getClientOnboardingStateVariant(client.onboardingState)" />
      </div>

      <p v-if="recommendedState !== client.onboardingState" class="text-xs text-text-muted">
        Based on the documents and verifications on file, this client can move toward
        <strong>{{ recommendedState }}</strong>.
      </p>
      <p v-else-if="availableTransitions.length === 0" class="text-xs text-text-muted">
        No further status changes are available from this status.
      </p>

      <div class="flex flex-wrap items-center gap-2">
        <BaseButton
          v-if="canAutoAdvance"
          size="sm"
          :icon="ArrowRightCircle"
          :loading="loading"
          @click="emit('autoAdvance')"
        >
          Advance
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
