<script setup lang="ts">
import { Building2, Pencil, Phone, Trash2, User } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

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

const { t } = useI18n()

const displayName = computed(() => getClientDisplayName(props.client))
const typeIcon = computed(() => (props.client.clientType === 'Individual' ? User : Building2))

const CLIENT_TYPE_LABEL_KEYS: Record<string, string> = {
  Individual: 'clientOptions.type.individual',
  Company: 'clientOptions.type.company',
  Organisation: 'clientOptions.type.organisation',
  'Government Entity': 'clientOptions.type.governmentEntity',
  Other: 'clientOptions.type.other',
}
const clientTypeLabel = computed(() => t(CLIENT_TYPE_LABEL_KEYS[props.client.clientType] ?? props.client.clientType))

const CLIENT_STATUS_LABEL_KEYS: Record<string, string> = {
  Active: 'clientOptions.status.active',
  Inactive: 'clientOptions.status.inactive',
}
const clientStatusLabel = computed(() => t(CLIENT_STATUS_LABEL_KEYS[props.client.status] ?? props.client.status))

const ONBOARDING_STATE_LABEL_KEYS: Record<string, string> = {
  'Information Required': 'clientOptions.onboardingState.informationRequired',
  'Documents Required': 'clientOptions.onboardingState.documentsRequired',
  'Under Review': 'clientOptions.onboardingState.underReview',
  Ready: 'clientOptions.onboardingState.ready',
  Rejected: 'clientOptions.onboardingState.rejected',
  Suspended: 'clientOptions.onboardingState.suspended',
}
const onboardingStateLabel = computed(() => t(ONBOARDING_STATE_LABEL_KEYS[props.client.onboardingState] ?? props.client.onboardingState))
</script>

<template>
  <div class="flex flex-col gap-4 rounded-xl border border-border-light bg-bg-card p-5 shadow-soft">
    <div class="flex flex-col gap-3 tablet:flex-row tablet:items-start tablet:justify-between">
      <div class="flex flex-col gap-1.5">
        <p class="text-xs font-medium uppercase tracking-wide text-text-muted">{{ client.code }} · {{ clientTypeLabel }}</p>
        <h1 class="text-xl font-semibold text-text-primary">{{ displayName }}</h1>
        <div class="flex flex-wrap items-center gap-4 text-sm text-text-muted">
          <span class="inline-flex items-center gap-1.5">
            <component :is="typeIcon" class="h-4 w-4 text-text-muted" />
            {{ client.contactPerson }}
          </span>
          <span class="inline-flex items-center gap-1.5">
            <Phone class="h-4 w-4 text-text-muted" />
            {{ client.mobile }}
          </span>
        </div>
      </div>

      <div class="flex shrink-0 flex-wrap items-center gap-2">
        <StatusBadge :label="onboardingStateLabel" :variant="getClientOnboardingStateVariant(client.onboardingState)" />
        <StatusBadge :label="clientStatusLabel" :variant="getClientStatusVariant(client.status)" />
        <BaseButton variant="secondary" size="sm" :loading="statusSaving" @click="$emit('toggle-status')">
          {{ client.status === 'Active' ? t('client.header.deactivate') : t('client.header.reactivate') }}
        </BaseButton>
        <IconButton :icon="Pencil" :label="t('client.header.editClient')" size="sm" @click="$emit('edit')" />
        <IconButton :icon="Trash2" :label="t('client.header.deleteClient')" size="sm" variant="danger" @click="$emit('delete')" />
      </div>
    </div>
  </div>
</template>
