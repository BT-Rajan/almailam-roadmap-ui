<script setup lang="ts">
import { ListChecks } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { ProjectActivityGroup } from '@/types/CustomerPortal'

defineProps<{
  activities: ProjectActivityGroup[]
}>()

const { t } = useI18n()
</script>

<template>
  <Card>
    <template #header>
      <h2 class="text-xl font-semibold text-text-primary">{{ t('customer.activitiesPanel.title') }}</h2>
    </template>

    <EmptyState
      v-if="activities.length === 0"
      :icon="ListChecks"
      :title="t('customer.activitiesPanel.emptyTitle')"
      :description="t('customer.activitiesPanel.emptyDescription')"
    />

    <div v-else class="flex flex-col gap-4">
      <div v-for="group in activities" :key="group.serviceName">
        <p class="text-sm font-semibold text-text-primary">{{ group.serviceName }}</p>
        <ul class="mt-1.5 flex flex-col gap-1">
          <li v-for="activity in group.activities" :key="activity" class="flex items-center gap-2 text-sm text-text-secondary">
            <span class="h-1.5 w-1.5 shrink-0 rounded-full bg-primary-400" />
            {{ activity }}
          </li>
        </ul>
      </div>
    </div>
  </Card>
</template>
