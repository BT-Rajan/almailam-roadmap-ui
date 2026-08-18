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
// the state should ultimately be -- calculated fresh from real data
// rather than trusted from whatever onboardingState happens to be
// stored (see utils/clientHelpers). This can (and very often does --
// e.g. right after a client is onboarded with a complete profile,
// documents, and verifications all in one sitting) land several steps
// ahead of the current state, since the backend's own transition graph
// only ever allows moving one step at a time.
const recommendedState = computed(() =>
  calculateOnboardingState(props.client, props.documents, props.contacts, props.addresses, props.verifications),
)

const availableTransitions = computed(
  () => CLIENT_ONBOARDING_ALLOWED_TRANSITIONS[props.client.onboardingState] ?? [],
)

// The pipeline's real forward order -- Rejected/Suspended are branches
// off it, not progress along it, so they're deliberately excluded here.
const PIPELINE_ORDER: ClientOnboardingState[] = [
  'Information Required',
  'Documents Required',
  'Verification Required',
  'Under Review',
  'Ready',
]

function pipelineIndex(state: ClientOnboardingState): number {
  return PIPELINE_ORDER.indexOf(state)
}

// The one-click "Advance" button needs to move the client ONE step
// closer to what the data supports, not require an exact match to the
// final recommended state -- previously it only ever offered the exact
// recommendedState as the target, so the button simply never appeared
// whenever that state was more than one step away, which is the common
// case (see above), not a rare edge case. This silently left every
// fully-ready client stuck showing "Information Required" forever,
// with no visible next action and no explanation -- staff had no way
// to tell it just needed to be manually stepped forward four times via
// "Change Status" instead of the one-click shortcut they were shown.
const nextStep = computed<ClientOnboardingState | null>(() => {
  const recommendedIndex = pipelineIndex(recommendedState.value)
  const currentIndex = pipelineIndex(props.client.onboardingState)
  if (recommendedIndex === -1 || currentIndex === -1 || recommendedIndex <= currentIndex) {
    return null
  }
  const forwardOptions = availableTransitions.value
    .filter((state) => {
      const index = pipelineIndex(state)
      return index > currentIndex && index <= recommendedIndex
    })
    .sort((a, b) => pipelineIndex(a) - pipelineIndex(b))
  return forwardOptions[0] ?? null
})

const canAutoAdvance = computed(() => nextStep.value !== null)
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
        Based on the documents and verifications on file, this client can move toward
        <strong>{{ recommendedState }}</strong>.
      </p>
      <p v-else-if="availableTransitions.length === 0" class="text-xs text-neutral-400">
        No further status changes are available from this status.
      </p>

      <div class="flex flex-wrap items-center gap-2">
        <BaseButton
          v-if="canAutoAdvance && nextStep"
          size="sm"
          :icon="ArrowRight"
          :loading="loading"
          @click="emit('advance', nextStep)"
        >
          Advance to {{ nextStep }}
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
