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
      <h3 class="text-sm font-semibold text-text-primary">Metadata</h3>
    </template>

    <dl class="flex flex-col gap-3 text-sm">
      <div class="flex items-center justify-between gap-3">
        <dt class="text-text-muted">Project</dt>
        <dd class="truncate text-right font-medium text-text-primary">{{ projectName }}</dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-text-muted">Category</dt>
        <dd class="font-medium text-text-primary">{{ document.type }}</dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-text-muted">Revision</dt>
        <dd class="font-medium text-text-primary">{{ document.revision }}</dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-text-muted">Status</dt>
        <dd><StatusBadge :label="document.status" :variant="getDocumentStatusVariant(document.status)" show-dot /></dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-text-muted">Uploaded By</dt>
        <dd class="font-medium text-text-primary">{{ document.uploadedBy }}</dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-text-muted">Upload Date</dt>
        <dd class="font-medium text-text-primary">{{ formatDate(document.uploadDate) }}</dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-text-muted">File Size</dt>
        <dd class="font-medium text-text-primary">{{ document.fileSize }}</dd>
      </div>
    </dl>
  </Card>
</template>
