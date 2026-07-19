<script setup lang="ts">
import { Check, Clock, FileCheck2 } from '@lucide/vue'
import type { Component } from 'vue'

import StatusBadge from '@/components/common/StatusBadge.vue'
import type { RequiredDocumentStatus, SubmissionDocument } from '@/types/Submission'
import { getDocumentStatusVariant } from '@/utils/submissionHelpers'

interface Props {
  documents: SubmissionDocument[]
}

defineProps<Props>()

const STATUS_ICONS: Record<RequiredDocumentStatus, Component> = {
  Pending: Clock,
  Uploaded: FileCheck2,
  Verified: Check,
}
</script>

<template>
  <ul class="flex flex-col divide-y divide-border-light">
    <li v-for="document in documents" :key="document.name" class="flex items-center justify-between gap-3 py-3">
      <span class="inline-flex items-center gap-2 text-sm text-neutral-700">
        <component :is="STATUS_ICONS[document.status]" class="h-4 w-4 text-neutral-400" />
        {{ document.name }}
      </span>
      <StatusBadge :label="document.status" :variant="getDocumentStatusVariant(document.status)" size="sm" />
    </li>
  </ul>
</template>
