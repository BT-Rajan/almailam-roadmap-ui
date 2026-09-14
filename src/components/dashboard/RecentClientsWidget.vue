<script setup lang="ts">
import { Building2 } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Card from '@/components/common/Card.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import type { BadgeVariant } from '@/types/Ui'
import type { RecentClient } from '@/types/Dashboard'
import { formatDate } from '@/utils/dateFormatter'

interface Props {
  clients: RecentClient[]
  title?: string
  maxItems?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: undefined,
  maxItems: 8,
})

const { t } = useI18n()

defineEmits<{
  'client-click': [clientId: string]
}>()

const displayedClients = computed(() =>
  [...props.clients].sort((a, b) => b.createdDate.localeCompare(a.createdDate)).slice(0, props.maxItems),
)

const statusVariant = (status: string): BadgeVariant => (status === 'Active' ? 'success' : 'neutral')
</script>

<template>
  <Card>
    <template #header>
      <h3 class="font-medium text-text-primary">{{ title ?? t('dashboard.recentClients') }}</h3>
    </template>

    <div v-if="displayedClients.length === 0" class="py-8 text-center text-text-muted">
      <p class="text-sm">{{ t('dashboard.noRecentClients') }}</p>
    </div>
    <div v-else class="space-y-2">
      <div
        v-for="client in displayedClients"
        :key="client.id"
        class="p-3 rounded-lg border border-border-light hover:bg-bg-hover transition-colors cursor-pointer flex items-start gap-3"
        @click="$emit('client-click', client.id)"
      >
        <Building2 class="h-5 w-5 text-text-muted flex-shrink-0 mt-0.5" />
        <div class="flex-1 min-w-0">
          <div class="flex items-start gap-2">
            <p class="text-sm font-medium text-text-primary flex-1 truncate">{{ client.name }}</p>
            <StatusBadge :label="client.status" :variant="statusVariant(client.status)" class="flex-shrink-0" />
          </div>
          <p class="text-xs text-text-muted mt-1">{{ client.type }} · {{ client.city }}</p>
          <p class="text-xs text-text-muted mt-1">{{ t('dashboard.addedOn', { date: formatDate(client.createdDate) }) }}</p>
        </div>
      </div>
    </div>
  </Card>
</template>
