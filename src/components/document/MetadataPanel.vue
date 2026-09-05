<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { DocumentStatus, ProjectDocument } from '@/types/Document'
import { formatDate } from '@/utils/dateFormatter'
import { getDocumentStatusVariant } from '@/utils/documentHelpers'

defineProps<{
  document: ProjectDocument
  projectName: string
}>()

const { t } = useI18n()

const STATUS_LABEL_KEYS: Record<DocumentStatus, string> = {
  Draft: 'document.status.draft',
  'Under Review': 'document.status.underReview',
  Approved: 'document.status.approved',
  Rejected: 'document.status.rejected',
}
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('document.metadataPanel.title') }}</h3>
    </template>

    <dl class="flex flex-col gap-3 text-sm">
      <div class="flex items-center justify-between gap-3">
        <dt class="text-text-muted">{{ t('document.metadataPanel.project') }}</dt>
        <dd class="truncate text-end font-medium text-text-primary">{{ projectName }}</dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-text-muted">{{ t('document.metadataPanel.category') }}</dt>
        <dd class="font-medium text-text-primary">{{ document.type }}</dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-text-muted">{{ t('document.metadataPanel.revision') }}</dt>
        <dd class="font-medium text-text-primary">{{ document.revision }}</dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-text-muted">{{ t('common.status') }}</dt>
        <dd><StatusBadge :label="t(STATUS_LABEL_KEYS[document.status])" :variant="getDocumentStatusVariant(document.status)" show-dot /></dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-text-muted">{{ t('document.metadataPanel.uploadedBy') }}</dt>
        <dd class="font-medium text-text-primary">{{ document.uploadedBy }}</dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-text-muted">{{ t('document.metadataPanel.uploadDate') }}</dt>
        <dd class="font-medium text-text-primary">{{ formatDate(document.uploadDate) }}</dd>
      </div>
      <div class="flex items-center justify-between gap-3">
        <dt class="text-text-muted">{{ t('document.metadataPanel.fileSize') }}</dt>
        <dd class="font-medium text-text-primary">{{ document.fileSize }}</dd>
      </div>
    </dl>
  </Card>
</template>
