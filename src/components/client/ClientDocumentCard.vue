<script setup lang="ts">
import { CalendarClock, Download, FileClock, FileText, Pencil, RefreshCw, ShieldCheck, Trash2, UserRound } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import IconButton from '@/components/common/IconButton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ClientDocument } from '@/types/Client'
import { formatDate } from '@/utils/dateFormatter'
import { getClientVerificationVariant } from '@/utils/clientHelpers'

const props = defineProps<{
  document: ClientDocument
}>()

const emit = defineEmits<{
  download: []
  verify: []
  edit: []
  delete: []
  history: []
  'replace-file': [file: File]
}>()

const { t } = useI18n()

const DOCUMENT_CATEGORY_LABEL_KEYS: Record<string, string> = {
  'Identity Document': 'clientOptions.documentCategory.identityDocument',
  Passport: 'clientOptions.documentCategory.passport',
  'Trade Licence': 'clientOptions.documentCategory.tradeLicence',
  'Registration Document': 'clientOptions.documentCategory.registrationDocument',
  'Authorisation Document': 'clientOptions.documentCategory.authorisationDocument',
  Other: 'clientOptions.documentCategory.other',
}
const categoryLabel = computed(() => t(DOCUMENT_CATEGORY_LABEL_KEYS[props.document.category] ?? props.document.category))

const VERIFICATION_STATUS_LABEL_KEYS: Record<string, string> = {
  Verified: 'clientOptions.verificationResult.verified',
  Rejected: 'clientOptions.verificationResult.rejected',
  Pending: 'clientOptions.verificationResult.pending',
}
const verificationStatusLabel = computed(() => t(VERIFICATION_STATUS_LABEL_KEYS[props.document.verificationStatus] ?? props.document.verificationStatus))

const fileInput = ref<HTMLInputElement>()

function triggerFileSelect(): void {
  fileInput.value?.click()
}

function handleFileChange(event: Event): void {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (file) emit('replace-file', file)
  ;(event.target as HTMLInputElement).value = ''
}
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
            <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ categoryLabel }} · v{{ document.version }}</p>
            <h3 class="text-sm font-semibold leading-snug text-text-primary">{{ document.title }}</h3>
          </div>
        </div>
        <div class="flex shrink-0 items-center gap-2">
          <StatusBadge :label="verificationStatusLabel" :variant="getClientVerificationVariant(document.verificationStatus)" show-dot />
          <IconButton :icon="ShieldCheck" :label="t('client.documentCard.recordVerification')" size="sm" @click="$emit('verify')" />
          <IconButton :icon="Download" :label="t('client.documentCard.download')" size="sm" @click="$emit('download')" />
          <IconButton :icon="FileClock" :label="t('client.documentCard.versionHistory')" size="sm" @click="$emit('history')" />
          <IconButton :icon="RefreshCw" :label="t('client.documentCard.replaceFile')" size="sm" @click="triggerFileSelect" />
          <IconButton :icon="Pencil" :label="t('client.documentCard.edit')" size="sm" @click="$emit('edit')" />
          <IconButton :icon="Trash2" :label="t('client.documentCard.remove')" size="sm" variant="danger" @click="$emit('delete')" />
          <input ref="fileInput" type="file" class="hidden" @change="handleFileChange" />
        </div>
      </div>

      <div v-if="document.issuingAuthority" class="text-sm text-text-muted">{{ document.issuingAuthority }}</div>

      <div class="flex items-center justify-between border-t border-border-light pt-3 text-xs text-text-muted">
        <div class="flex items-center gap-1.5">
          <UserRound class="h-3.5 w-3.5" />
          <span>{{ document.uploadedBy }}</span>
        </div>
        <div class="flex items-center gap-3">
          <span>{{ document.originalFilename }} · {{ document.fileSize }}</span>
          <span class="inline-flex items-center gap-1.5">
            <CalendarClock class="h-3.5 w-3.5" />
            {{ formatDate(document.uploadDate) }}
          </span>
        </div>
      </div>
    </div>
  </Card>
</template>
