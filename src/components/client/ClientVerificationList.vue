<script setup lang="ts">
import { ShieldAlert } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ClientVerification } from '@/types/Client'
import { formatDate } from '@/utils/dateFormatter'
import { getClientVerificationVariant } from '@/utils/clientHelpers'

defineProps<{
  verifications: ClientVerification[]
}>()
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-neutral-800">Verification Records</h3>
    </template>

    <EmptyState
      v-if="verifications.length === 0"
      :icon="ShieldAlert"
      title="No verification records"
      description="Verification checks recorded for this client will appear here."
    />

    <ul v-else class="flex flex-col divide-y divide-border-light">
      <li v-for="verification in verifications" :key="verification.id" class="flex flex-col gap-1.5 py-3">
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm font-medium text-neutral-800">{{ verification.item }}</span>
          <StatusBadge :label="verification.result" :variant="getClientVerificationVariant(verification.result)" size="sm" />
        </div>
        <p class="text-xs text-neutral-500">
          {{ verification.verifiedBy }} · {{ formatDate(verification.verifiedDate) }}
        </p>
        <p v-if="verification.notes" class="text-xs text-neutral-500">{{ verification.notes }}</p>
      </li>
    </ul>
  </Card>
</template>
