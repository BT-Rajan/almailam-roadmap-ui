<script setup lang="ts">
import { Pencil, ShieldCheck, Trash2, UserRound } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import IconButton from '@/components/common/IconButton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ClientContact } from '@/types/Client'

defineProps<{
  contacts: ClientContact[]
}>()

defineEmits<{
  edit: [contact: ClientContact]
  delete: [contact: ClientContact]
}>()

const { t } = useI18n()

const CONTACT_TYPE_LABEL_KEYS: Record<string, string> = {
  'Primary Contact': 'clientOptions.contactType.primary',
  'Billing Contact': 'clientOptions.contactType.billing',
  'Legal Contact': 'clientOptions.contactType.legal',
  'Authorised Representative': 'clientOptions.contactType.authorisedRepresentative',
  'Technical Contact': 'clientOptions.contactType.technical',
  Other: 'clientOptions.contactType.other',
}
function contactTypeLabel(contactType: string): string {
  return t(CONTACT_TYPE_LABEL_KEYS[contactType] ?? contactType)
}
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">{{ t('client.contactList.title') }}</h3>
    </template>

    <EmptyState
      v-if="contacts.length === 0"
      :icon="UserRound"
      :title="t('client.contactList.emptyTitle')"
      :description="t('client.contactList.emptyDescription')"
    />

    <ul v-else class="flex flex-col divide-y divide-border-light">
      <li v-for="contact in contacts" :key="contact.id" class="flex items-center justify-between gap-3 py-3">
        <div class="flex items-center gap-3">
          <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary-50 text-primary-600">
            <UserRound class="h-4 w-4" />
          </span>
          <div class="flex flex-col">
            <span class="inline-flex items-center gap-1.5 text-sm font-medium text-text-primary">
              {{ contact.name }}
              <ShieldCheck v-if="contact.isAuthorisedRepresentative" class="h-3.5 w-3.5 text-success-500" aria-hidden="true" />
              <span v-if="contact.isAuthorisedRepresentative" class="sr-only">{{ t('client.contactList.authorisedRepresentative') }}</span>
            </span>
            <span class="text-xs text-text-muted">{{ contact.mobile }} · {{ contact.email }}</span>
          </div>
        </div>
        <div class="flex shrink-0 items-center gap-2">
          <StatusBadge :label="contactTypeLabel(contact.contactType)" variant="info" size="sm" />
          <IconButton :icon="Pencil" :label="t('client.contactList.edit', { name: contact.name })" size="sm" @click="$emit('edit', contact)" />
          <IconButton :icon="Trash2" :label="t('client.contactList.remove', { name: contact.name })" size="sm" variant="danger" @click="$emit('delete', contact)" />
        </div>
      </li>
    </ul>
  </Card>
</template>
