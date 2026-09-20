<script setup lang="ts">
import { Building2, ChevronLeft, ChevronRight } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import PaginatedList from '@/components/common/PaginatedList.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import { useLocale } from '@/composables/useLocale'
import type { BadgeVariant } from '@/types/Ui'
import type { RecentClient } from '@/types/Dashboard'
import { formatDate } from '@/utils/dateFormatter'

interface Props {
  clients: RecentClient[]
  title?: string
  pageSize?: number
}

const props = withDefaults(defineProps<Props>(), {
  title: undefined,
  pageSize: 10,
})

const { t } = useI18n()
const { isRtl } = useLocale()
const chevronIcon = computed(() => (isRtl.value ? ChevronLeft : ChevronRight))

defineEmits<{
  'client-click': [clientId: string]
}>()

const displayedClients = computed(() =>
  [...props.clients].sort((a, b) => b.createdDate.localeCompare(a.createdDate)),
)

const statusVariant = (status: string): BadgeVariant => (status === 'Active' ? 'success' : 'neutral')
</script>

<template>
  <Card :padded="false">
    <template #header>
      <h3 class="text-center text-sm font-semibold text-text-primary">{{ title ?? t('dashboard.recentClients') }}</h3>
    </template>

    <EmptyState v-if="displayedClients.length === 0" :title="t('dashboard.noRecentClients')" :bordered="false" />
    <PaginatedList v-else :items="displayedClients" :page-size="pageSize" pager-inset="card">
      <template #default="{ items }">
        <ul class="divide-y divide-border-light">
          <li
            v-for="client in items"
            :key="client.id"
            class="flex cursor-pointer items-center gap-3 px-5 py-3.5 transition-colors hover:bg-bg-hover"
            @click="$emit('client-click', client.id)"
          >
            <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-bg-secondary">
              <Building2 class="h-5 w-5 text-text-muted" />
            </span>
            <div class="min-w-0 flex-1">
              <div class="flex items-start gap-2">
                <p class="flex-1 truncate text-sm font-medium text-text-primary">{{ client.name }}</p>
                <StatusBadge :label="client.status" :variant="statusVariant(client.status)" class="shrink-0" />
              </div>
              <p class="mt-0.5 truncate text-xs text-text-muted">{{ client.type }} · {{ client.city }}</p>
              <p class="mt-1.5 text-xs text-text-muted">{{ t('dashboard.addedOn', { date: formatDate(client.createdDate) }) }}</p>
            </div>
            <component :is="chevronIcon" class="h-4 w-4 shrink-0 text-text-muted" />
          </li>
        </ul>
      </template>
    </PaginatedList>
  </Card>
</template>
