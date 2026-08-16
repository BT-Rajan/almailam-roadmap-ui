<script setup lang="ts">
import { AlertTriangle, IdCard } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ClientIdentification } from '@/types/Client'
import { formatDate } from '@/utils/dateFormatter'
import { isIdentificationExpired } from '@/utils/clientHelpers'

defineProps<{
  identifications: ClientIdentification[]
}>()
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-neutral-800">Identification</h3>
    </template>

    <EmptyState
      v-if="identifications.length === 0"
      :icon="IdCard"
      title="No identification on file"
      description="Identification or licence documents recorded for this client will appear here."
    />

    <ul v-else class="flex flex-col divide-y divide-border-light">
      <li v-for="identification in identifications" :key="identification.id" class="flex flex-col gap-1.5 py-3">
        <div class="flex items-center justify-between gap-3">
          <span class="inline-flex items-center gap-2 text-sm font-medium text-neutral-800">
            <IdCard class="h-4 w-4 shrink-0 text-neutral-400" />
            {{ identification.documentType }}
          </span>
          <StatusBadge
            v-if="isIdentificationExpired(identification.expiryDate)"
            label="Expired"
            variant="danger"
            size="sm"
          />
        </div>
        <p class="text-sm text-neutral-700">{{ identification.documentNumber }}</p>
        <p class="inline-flex items-center gap-1.5 text-xs text-neutral-500">
          <AlertTriangle v-if="isIdentificationExpired(identification.expiryDate)" class="h-3.5 w-3.5 text-danger-500" />
          Issued {{ formatDate(identification.issueDate) }} · Expires {{ formatDate(identification.expiryDate) }} · {{ identification.issuingCountry }}
        </p>
      </li>
    </ul>
  </Card>
</template>
