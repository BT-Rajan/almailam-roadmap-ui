<script setup lang="ts">
import { Building2, Pencil, Phone, Trash2, User } from '@lucide/vue'
import { computed } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import IconButton from '@/components/common/IconButton.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { Client } from '@/types/Client'
import { getClientDisplayName, getClientOnboardingStateVariant, getClientStatusVariant } from '@/utils/clientHelpers'

const props = defineProps<{
  client: Client
  statusSaving?: boolean
}>()

defineEmits<{
  edit: []
  'toggle-status': []
  delete: []
}>()

const displayName = computed(() => getClientDisplayName(props.client))
const typeIcon = computed(() => (props.client.clientType === 'Individual' ? User : Building2))
</script>

<template>
  <div class="flex flex-col gap-4 rounded-xl border border-border-light bg-bg-card p-5 shadow-soft">
    <div class="flex flex-col gap-3 tablet:flex-row tablet:items-start tablet:justify-between">
      <div class="flex flex-col gap-1.5">
        <p class="text-xs font-medium uppercase tracking-wide text-neutral-400">{{ client.code }} · {{ client.clientType }}</p>
        <h1 class="text-xl font-semibold text-neutral-800">{{ displayName }}</h1>
        <div class="flex flex-wrap items-center gap-4 text-sm text-neutral-500">
          <span class="inline-flex items-center gap-1.5">
            <component :is="typeIcon" class="h-4 w-4 text-neutral-400" />
            {{ client.contactPerson }}
          </span>
          <span class="inline-flex items-center gap-1.5">
            <Phone class="h-4 w-4 text-neutral-400" />
            {{ client.mobile }}
          </span>
        </div>
      </div>

      <div class="flex shrink-0 flex-wrap items-center gap-2">
        <StatusBadge :label="client.onboardingState" :variant="getClientOnboardingStateVariant(client.onboardingState)" />
        <StatusBadge :label="client.status" :variant="getClientStatusVariant(client.status)" />
        <BaseButton variant="secondary" size="sm" :loading="statusSaving" @click="$emit('toggle-status')">
          {{ client.status === 'Active' ? 'Deactivate' : 'Reactivate' }}
        </BaseButton>
        <IconButton :icon="Pencil" label="Edit client" size="sm" @click="$emit('edit')" />
        <IconButton :icon="Trash2" label="Delete client" size="sm" variant="danger" @click="$emit('delete')" />
      </div>
    </div>
  </div>
</template>
