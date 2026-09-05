<script setup lang="ts">
import { AlertTriangle, Eye, IdCard, Pencil, Trash2 } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { getDocumentCategoryForIdentificationType } from '@/constants/clientOptions'
import type { ClientDocument, ClientIdentification } from '@/types/Client'
import { formatDate } from '@/utils/dateFormatter'
import { isIdentificationExpired } from '@/utils/clientHelpers'

const props = defineProps<{
  identifications: ClientIdentification[]
  documents: ClientDocument[]
}>()

defineEmits<{
  edit: [identification: ClientIdentification]
  delete: [identification: ClientIdentification]
  view: [document: ClientDocument]
}>()

const { t } = useI18n()

const IDENTIFICATION_TYPE_LABEL_KEYS: Record<string, string> = {
  'Civil ID': 'clientOptions.identificationType.civilId',
  Passport: 'clientOptions.identificationType.passport',
  'Trade Licence': 'clientOptions.identificationType.tradeLicence',
  Other: 'clientOptions.identificationType.other',
}
function identificationTypeLabel(documentType: string): string {
  return t(IDENTIFICATION_TYPE_LABEL_KEYS[documentType] ?? documentType)
}

// Identification records and the uploaded file are separate entities on
// the backend (no direct FK -- see clientStore.createIdentification vs.
// createDocument in NewClientWizardPage.vue), only linked implicitly by
// the document category the identification type maps to. Best-effort
// match on category, picking the most recently uploaded copy if there's
// more than one -- good enough to put a "View" button next to the
// identification it belongs to without inventing a new backend link.
function matchedDocument(identification: ClientIdentification): ClientDocument | undefined {
  const category = getDocumentCategoryForIdentificationType(identification.documentType)
  return props.documents
    .filter((document) => document.category === category)
    .sort((a, b) => (a.uploadDate < b.uploadDate ? 1 : -1))[0]
}
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('client.identificationList.title') }}</h3>
    </template>

    <EmptyState
      v-if="identifications.length === 0"
      :icon="IdCard"
      :title="t('client.identificationList.emptyTitle')"
      :description="t('client.identificationList.emptyDescription')"
    />

    <ul v-else class="flex flex-col divide-y divide-border-light">
      <li v-for="identification in identifications" :key="identification.id" class="flex flex-col gap-1.5 py-3">
        <div class="flex items-center justify-between gap-3">
          <span class="inline-flex items-center gap-2 text-sm font-medium text-text-primary">
            <IdCard class="h-4 w-4 shrink-0 text-text-muted" />
            {{ identificationTypeLabel(identification.documentType) }}
          </span>
          <div class="flex shrink-0 items-center gap-2">
            <StatusBadge
              v-if="isIdentificationExpired(identification.expiryDate)"
              :label="t('client.identificationList.expired')"
              variant="danger"
              size="sm"
            />
            <IconButton
              v-if="matchedDocument(identification)"
              :icon="Eye"
              :label="t('client.identificationList.viewDocument')"
              size="sm"
              @click="$emit('view', matchedDocument(identification)!)"
            />
            <IconButton :icon="Pencil" :label="t('client.identificationList.edit')" size="sm" @click="$emit('edit', identification)" />
            <IconButton :icon="Trash2" :label="t('client.identificationList.remove')" size="sm" variant="danger" @click="$emit('delete', identification)" />
          </div>
        </div>
        <p class="text-sm text-text-secondary">{{ identification.documentNumber }}</p>
        <p class="inline-flex items-center gap-1.5 text-xs text-text-muted">
          <AlertTriangle v-if="isIdentificationExpired(identification.expiryDate)" class="h-3.5 w-3.5 text-danger-500" />
          {{ t('client.identificationList.summary', { issueDate: formatDate(identification.issueDate), expiryDate: formatDate(identification.expiryDate), country: identification.issuingCountry }) }}
        </p>
      </li>
    </ul>
  </Card>
</template>
