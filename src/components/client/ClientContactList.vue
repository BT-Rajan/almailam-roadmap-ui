<script setup lang="ts">
import { Pencil, ShieldCheck, Trash2, UserRound } from '@lucide/vue'

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
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-text-primary">Contacts</h3>
    </template>

    <EmptyState
      v-if="contacts.length === 0"
      :icon="UserRound"
      title="No contacts on file"
      description="Add a primary contact so this client can be reached during onboarding."
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
              <ShieldCheck v-if="contact.isAuthorisedRepresentative" class="h-3.5 w-3.5 text-success-500" />
            </span>
            <span class="text-xs text-text-muted">{{ contact.mobile }} · {{ contact.email }}</span>
          </div>
        </div>
        <div class="flex shrink-0 items-center gap-2">
          <StatusBadge :label="contact.contactType" variant="info" size="sm" />
          <IconButton :icon="Pencil" label="Edit contact" size="sm" @click="$emit('edit', contact)" />
          <IconButton :icon="Trash2" label="Remove contact" size="sm" variant="danger" @click="$emit('delete', contact)" />
        </div>
      </li>
    </ul>
  </Card>
</template>
