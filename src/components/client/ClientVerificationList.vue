<script setup lang="ts">
import { ShieldAlert } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ClientVerification } from '@/types/Client'
import { formatDate } from '@/utils/dateFormatter'
import { getClientVerificationVariant } from '@/utils/clientHelpers'

defineProps<{
  verifications: ClientVerification[]
}>()

const { t } = useI18n()

const VERIFICATION_RESULT_LABEL_KEYS: Record<string, string> = {
  Verified: 'clientOptions.verificationResult.verified',
  Rejected: 'clientOptions.verificationResult.rejected',
  Pending: 'clientOptions.verificationResult.pending',
}
function verificationResultLabel(result: string): string {
  return t(VERIFICATION_RESULT_LABEL_KEYS[result] ?? result)
}
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('client.verificationList.title') }}</h3>
    </template>

    <EmptyState
      v-if="verifications.length === 0"
      :icon="ShieldAlert"
      :title="t('client.verificationList.emptyTitle')"
      :description="t('client.verificationList.emptyDescription')"
    />

    <ul v-else class="flex flex-col divide-y divide-border-light">
      <li v-for="verification in verifications" :key="verification.id" class="flex flex-col gap-1.5 py-3">
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm font-medium text-text-primary">{{ verification.item }}</span>
          <StatusBadge :label="verificationResultLabel(verification.result)" :variant="getClientVerificationVariant(verification.result)" size="sm" />
        </div>
        <p class="text-xs text-text-muted">
          {{ verification.verifiedBy }} · {{ formatDate(verification.verifiedDate) }}
        </p>
        <p v-if="verification.notes" class="text-xs text-text-muted">{{ verification.notes }}</p>
      </li>
    </ul>
  </Card>
</template>
