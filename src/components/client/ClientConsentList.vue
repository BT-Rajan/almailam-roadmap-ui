<script setup lang="ts">
import { ShieldCheck } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ClientConsent } from '@/types/Client'
import { formatDateTime } from '@/utils/dateFormatter'

defineProps<{
  consents: ClientConsent[]
}>()
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
      <li v-for="consent in consents" :key="consent.id" class="flex items-center justify-between gap-3 py-3">
        <div class="flex flex-col gap-1">
          <span class="text-sm font-medium text-neutral-800">{{ consent.consentType }}</span>
          <span class="text-xs text-neutral-500">
            {{ consent.method }} · {{ formatDateTime(consent.dateTime) }} · Recorded by {{ consent.recordedBy }}
          </span>
        </div>
        <StatusBadge :label="consent.granted ? 'Granted' : 'Withdrawn'" :variant="consent.granted ? 'success' : 'danger'" size="sm" />
      </li>
    </ul>
  </Card>
</template>
