<script setup lang="ts">
import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ProjectDocument } from '@/types/Document'
import { formatDate } from '@/utils/dateFormatter'
import { getDocumentStatusVariant } from '@/utils/documentHelpers'

defineProps<{
  document: ProjectDocument
  projectName: string
}>()
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-neutral-800">Metadata</h3>
    </template>

    <dl class="flex flex-col gap-3 text-sm">
      <div class="flex items-center justify-between gap-3">
        <dt class="text-neutral-500">Project</dt>
        <dd class="truncate text-right font-medium text-neutral-800">{{ projectName }}</dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-neutral-500">Category</dt>
        <dd class="font-medium text-neutral-800">{{ document.type }}</dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-neutral-500">Revision</dt>
        <dd class="font-medium text-neutral-800">{{ document.revision }}</dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-neutral-500">Status</dt>
        <dd><StatusBadge :label="document.status" :variant="getDocumentStatusVariant(document.status)" show-dot /></dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-neutral-500">Uploaded By</dt>
        <dd class="font-medium text-neutral-800">{{ document.uploadedBy }}</dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-neutral-500">Upload Date</dt>
        <dd class="font-medium text-neutral-800">{{ formatDate(document.uploadDate) }}</dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-neutral-500">File Size</dt>
        <dd class="font-medium text-neutral-800">{{ document.fileSize }}</dd>
      </div>
    </dl>
  </Card>
</template>
