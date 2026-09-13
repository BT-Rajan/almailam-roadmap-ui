<script setup lang="ts">
import { Eye, IdCard } from '@lucide/vue'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseDialog from '@/components/common/BaseDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import ClientProjectDocumentsPanel from '@/components/client/ClientProjectDocumentsPanel.vue'
import { useClientStore } from '@/stores/clientStore'
import { useProjectStore } from '@/stores/projectStore'
import type { Client, ClientDocumentCategory } from '@/types/Client'
import { formatDate } from '@/utils/dateFormatter'
import { getClientFormalName } from '@/utils/clientHelpers'

const props = defineProps<{
  modelValue: boolean
  client?: Client
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const { t } = useI18n()
const clientStore = useClientStore()
const projectStore = useProjectStore()

const isLoading = ref(false)

// Every uploaded client document, unfiltered -- shown alongside (not
// instead of) the structured identification records below. Matching a
// document to a specific identification record by category alone is a
// heuristic that silently drops a document the moment it's filed under
// a category that doesn't line up (e.g. a Civil ID scan uploaded as
// 'Other') -- this list can't miss anything because it doesn't try to
// match at all, it just shows what's actually there.
const clientDocuments = computed(() => clientStore.documents)
const clientIdentifications = computed(() => clientStore.identifications)

const clientProjects = computed(() => {
  if (!props.client) return []
  return projectStore.projects.filter((project) => project.clientId === props.client!.id)
})

const CATEGORY_LABEL_KEYS: Record<ClientDocumentCategory, string> = {
  'Identity Document': 'clientOptions.documentCategory.identityDocument',
  Passport: 'clientOptions.documentCategory.passport',
  'Trade Licence': 'clientOptions.documentCategory.tradeLicence',
  'Registration Document': 'clientOptions.documentCategory.registrationDocument',
  'Authorisation Document': 'clientOptions.documentCategory.authorisationDocument',
  Other: 'clientOptions.documentCategory.other',
}

async function loadData(): Promise<void> {
  if (!props.client) return
  isLoading.value = true
  try {
    await Promise.all([clientStore.loadClientDetail(props.client.id), projectStore.loadProjects()])
  } finally {
    isLoading.value = false
  }
}

watch(
  () => [props.modelValue, props.client?.id] as const,
  ([isOpen]) => {
    if (isOpen) void loadData()
  },
)

function viewDocument(documentId: string): void {
  if (!props.client) return
  void clientStore.viewDocument(props.client.id, documentId)
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="client ? getClientFormalName(client) : undefined"
    size="lg"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <SkeletonLoader v-if="isLoading" :rows="5" />

    <div v-else class="flex flex-col gap-6">
      <section class="flex flex-col gap-3">
        <h3 class="text-sm font-semibold text-text-primary">{{ t('client.workspacePage.identification') }}</h3>

        <ul
          v-if="clientIdentifications.length > 0"
          class="flex flex-col divide-y divide-border-light rounded-lg border border-border-light"
        >
          <li v-for="identification in clientIdentifications" :key="identification.id" class="flex flex-col gap-0.5 px-3 py-2.5">
            <span class="text-sm text-text-primary">{{ identification.documentType }} &ndash; {{ identification.documentNumber }}</span>
            <span class="text-xs text-text-muted">
              {{
                t('client.identificationList.summary', {
                  issueDate: formatDate(identification.issueDate),
                  expiryDate: formatDate(identification.expiryDate),
                  country: identification.issuingCountry,
                })
              }}
            </span>
          </li>
        </ul>

        <!-- Every uploaded document for this client -- title, category,
             and its own upload date -- so an uploaded Civil ID (or any
             other scan) always shows here even if it isn't linked to a
             matching identification record above. -->
        <ul
          v-if="clientDocuments.length > 0"
          class="flex flex-col divide-y divide-border-light rounded-lg border border-border-light"
        >
          <li v-for="document in clientDocuments" :key="document.id" class="flex items-center justify-between gap-3 px-3 py-2.5">
            <span class="flex flex-col gap-0.5">
              <span class="text-sm text-text-primary">{{ document.title }}</span>
              <span class="text-xs text-text-muted">
                {{ t(CATEGORY_LABEL_KEYS[document.category]) }} &middot; {{ formatDate(document.uploadDate) }}
              </span>
            </span>
            <IconButton :icon="Eye" :label="t('document.card.viewDocument')" size="sm" @click="viewDocument(document.id)" />
          </li>
        </ul>

        <EmptyState
          v-if="clientIdentifications.length === 0 && clientDocuments.length === 0"
          :icon="IdCard"
          :title="t('client.identificationList.emptyTitle')"
          :description="t('client.identificationList.emptyDescription')"
        />
      </section>

      <section class="flex flex-col gap-3">
        <h3 class="text-sm font-semibold text-text-primary">{{ t('client.projectDocuments.title') }}</h3>
        <ClientProjectDocumentsPanel :projects="clientProjects" bare />
      </section>
    </div>
  </BaseDialog>
</template>
