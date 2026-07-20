<script setup lang="ts">
import { CalendarClock, FileText, UserRound } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ClientDocument } from '@/types/Client'
import { formatDate } from '@/utils/dateFormatter'
import { getClientVerificationVariant } from '@/utils/clientHelpers'

defineProps<{
  document: ClientDocument
}>()
</script>

<template>
  <Card>
    <div class="flex flex-col gap-4">
      <div class="flex items-start justify-between gap-3">
        <div class="flex items-start gap-3">
          <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary-50">
            <FileText class="h-5 w-5 text-primary-600" />
          </span>
          <div class="flex flex-col gap-1">
            <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">{{ document.category }} · v{{ document.version }}</p>
            <h3 class="text-sm font-semibold leading-snug text-neutral-800">{{ document.title }}</h3>
          </div>
        </div>
        <StatusBadge :label="document.verificationStatus" :variant="getClientVerificationVariant(document.verificationStatus)" show-dot />
      </div>

      <div v-if="document.issuingAuthority" class="text-sm text-neutral-500">{{ document.issuingAuthority }}</div>

      <div class="flex items-center justify-between border-t border-border-light pt-3 text-xs text-neutral-500">
        <div class="flex items-center gap-1.5">
          <UserRound class="h-3.5 w-3.5" />
          <span>{{ document.uploadedBy }}</span>
        </div>
        <div class="flex items-center gap-1.5">
          <CalendarClock class="h-3.5 w-3.5" />
          <span>{{ formatDate(document.uploadDate) }}</span>
        </div>
      </div>
    </div>
  </Card>
</template>
