<script setup lang="ts">
import { ShieldCheck, UserRound } from '@lucide/vue'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { ClientContact } from '@/types/Client'

defineProps<{
  contacts: ClientContact[]
}>()
</script>

<template>
  <Card>
    <template #header>
      <h3 class="text-sm font-semibold text-neutral-800">Contacts</h3>
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
            <span class="inline-flex items-center gap-1.5 text-sm font-medium text-neutral-800">
              {{ contact.name }}
              <ShieldCheck v-if="contact.isAuthorisedRepresentative" class="h-3.5 w-3.5 text-success-500" />
            </span>
            <span class="text-xs text-neutral-500">{{ contact.mobile }} · {{ contact.email }}</span>
          </div>
        </div>
        <StatusBadge :label="contact.contactType" variant="info" size="sm" />
      </li>
    </ul>
  </Card>
</template>
