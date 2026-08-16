<script setup lang="ts">
import { ShieldCheck } from '@lucide/vue'
import { computed } from 'vue'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ClientConsent } from '@/types/Client'
import { formatDateTime } from '@/utils/dateFormatter'

const props = defineProps<{
  consents: ClientConsent[]
}>()

// Consent records are append-only history, not edited in place -- so a
// `granted: false` row means one of two different things depending on
// what came before it for that same consent type:
//   - no earlier record ever had granted: true  -> this was simply
//     declined when first asked ("Declined")
//   - an earlier record for the same type had granted: true -> consent
//     was later taken back ("Withdrawn")
// Collapsing both into "Withdrawn" (as if something was always granted
// then revoked) misdescribes the common case, which is just an onboarding
// decline.
function labelFor(consent: ClientConsent): string {
  if (consent.granted) return 'Granted'
  const wasEverGranted = props.consents.some(
    (other) =>
      other.consentType === consent.consentType &&
      other.granted &&
      new Date(other.dateTime).getTime() < new Date(consent.dateTime).getTime(),
  )
  return wasEverGranted ? 'Withdrawn' : 'Declined'
}

const rows = computed(() => props.consents.map((consent) => ({ consent, label: labelFor(consent) })))
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-neutral-800">Consent Records</h3>
    </template>

    <EmptyState
      v-if="consents.length === 0"
      :icon="ShieldCheck"
      title="No consent recorded"
      description="Consent captured during onboarding will appear here for audit purposes."
    />

    <ul v-else class="flex flex-col divide-y divide-border-light">
      <li v-for="{ consent, label } in rows" :key="consent.id" class="flex items-center justify-between gap-3 py-3">
        <div class="flex flex-col gap-1">
          <span class="text-sm font-medium text-neutral-800">{{ consent.consentType }}</span>
          <span class="text-xs text-neutral-500">
            {{ consent.method }} · {{ formatDateTime(consent.dateTime) }} · Recorded by {{ consent.recordedBy }}
          </span>
        </div>
        <StatusBadge :label="label" :variant="consent.granted ? 'success' : 'danger'" size="sm" />
      </li>
    </ul>
  </Card>
</template>
