<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { governmentSubmissionService } from '@/services/governmentSubmissionService'
import { useGovernmentSubmissionStore } from '@/stores/governmentSubmissionStore'
import { useToastStore } from '@/stores/toastStore'
import type { DocumentCandidate, DocumentSourceType, SubmissionDocument } from '@/types/Submission'
import { formatDate } from '@/utils/dateFormatter'

// "Pick from documents on file" for one checklist entry: the project's
// documents, the client's documents, the project's link documents, and
// files already attached to other applications on the project -- so a
// file is uploaded once and reused. Attaching points the entry at the
// same stored file/link; nothing is copied.
const props = defineProps<{
  modelValue: boolean
  submissionNo: string
  document: SubmissionDocument | undefined
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const { t } = useI18n()
const submissionStore = useGovernmentSubmissionStore()
const toastStore = useToastStore()

const candidates = ref<DocumentCandidate[]>([])
const isLoading = ref(false)
const loadError = ref<string>()
const isAttaching = ref(false)
const selectedKey = ref<string>()

const SOURCE_LABEL_KEYS: Record<DocumentSourceType, string> = {
  project: 'government.attachDocumentDialog.sourceProject',
  client: 'government.attachDocumentDialog.sourceClient',
  link: 'government.attachDocumentDialog.sourceLink',
  application: 'government.attachDocumentDialog.sourceApplication',
}

function keyOf(candidate: DocumentCandidate): string {
  return `${candidate.sourceType}:${candidate.sourceId}`
}

const selected = computed(() => candidates.value.find((candidate) => keyOf(candidate) === selectedKey.value))

async function load(): Promise<void> {
  if (!props.document) return
  isLoading.value = true
  loadError.value = undefined
  selectedKey.value = undefined
  candidates.value = []
  try {
    candidates.value = await governmentSubmissionService.getDocumentCandidates(props.submissionNo, props.document.id)
    // The likeliest match is preselected -- one click to confirm.
    const first = candidates.value[0]
    if (first?.suggested) selectedKey.value = keyOf(first)
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : t('common.pleaseTryAgain')
  } finally {
    isLoading.value = false
  }
}

watch(
  () => props.modelValue,
  (open) => {
    if (open) load()
  },
)

function isExpired(candidate: DocumentCandidate): boolean {
  if (!candidate.expiryDate) return false
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return new Date(candidate.expiryDate) < today
}

function detailLine(candidate: DocumentCandidate): string {
  const parts: string[] = [t(SOURCE_LABEL_KEYS[candidate.sourceType])]
  if (candidate.fromApplication) parts.push(candidate.fromApplication)
  else if (candidate.category) parts.push(candidate.category)
  if (candidate.filename) parts.push(candidate.filename)
  else if (candidate.externalLink) parts.push(t('government.attachDocumentDialog.link'))
  if (candidate.fileSizeLabel) parts.push(candidate.fileSizeLabel)
  if (candidate.onDate) parts.push(formatDate(candidate.onDate))
  return parts.join(' · ')
}

function close(): void {
  if (isAttaching.value) return
  emit('update:modelValue', false)
}

async function attach(): Promise<void> {
  const choice = selected.value
  if (!choice || !props.document) return
  isAttaching.value = true
  const success = await submissionStore.attachDocument(props.submissionNo, props.document.id, choice.sourceType, choice.sourceId)
  isAttaching.value = false
  if (success) {
    toastStore.show(
      'success',
      t('government.attachDocumentDialog.attachedTitle'),
      t('government.attachDocumentDialog.attachedDescription', { name: props.document.name }),
    )
    emit('update:modelValue', false)
  } else {
    toastStore.show('error', t('government.attachDocumentDialog.failedToAttach'), submissionStore.mutationError ?? t('common.pleaseTryAgain'))
  }
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="t('government.attachDocumentDialog.title', { name: document?.name ?? '' })"
    size="md"
    :closable="!isAttaching"
    @update:model-value="close"
  >
    <SkeletonLoader v-if="isLoading" :rows="4" />

    <p v-else-if="loadError" class="text-sm text-danger-700" role="alert">{{ loadError }}</p>

    <EmptyState
      v-else-if="candidates.length === 0"
      :title="t('government.attachDocumentDialog.emptyTitle')"
      :description="t('government.attachDocumentDialog.emptyDescription')"
    />

    <ul v-else class="flex max-h-[55vh] flex-col gap-2 overflow-y-auto" role="radiogroup" :aria-label="t('government.attachDocumentDialog.listLabel')">
      <li v-for="candidate in candidates" :key="keyOf(candidate)">
        <label
          class="flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors duration-fast focus-within:ring-2 focus-within:ring-accent-500/30"
          :class="selectedKey === keyOf(candidate) ? 'border-accent-500 bg-accent-500/5' : 'border-border-light hover:bg-bg-secondary'"
        >
          <input v-model="selectedKey" type="radio" name="document-on-file" class="mt-1" :value="keyOf(candidate)" />
          <span class="flex min-w-0 flex-1 flex-col gap-0.5">
            <span class="flex flex-wrap items-center gap-2">
              <span class="truncate text-sm font-medium text-text-primary">{{ candidate.title }}</span>
              <StatusBadge v-if="candidate.suggested" :label="t('government.attachDocumentDialog.suggested')" variant="primary" size="sm" />
              <StatusBadge v-if="isExpired(candidate)" :label="t('government.attachDocumentDialog.expired')" variant="warning" size="sm" />
            </span>
            <span class="truncate text-xs text-text-muted">{{ detailLine(candidate) }}</span>
          </span>
        </label>
      </li>
    </ul>

    <template #footer>
      <BaseButton variant="secondary" :disabled="isAttaching" @click="close">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :disabled="!selected" :loading="isAttaching" @click="attach">{{ t('government.attachDocumentDialog.attach') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
