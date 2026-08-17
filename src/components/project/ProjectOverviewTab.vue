<script setup lang="ts">
import { MessageSquare } from '@lucide/vue'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import DetailPanel from '@/components/common/DetailPanel.vue'
import { ROUTE_NAMES } from '@/constants/routeNames'
import type { Client } from '@/types/Client'
import type { Project } from '@/types/Project'
import { formatDate } from '@/utils/dateFormatter'

const props = defineProps<{
  project: Project
  client: Client | undefined
}>()

const router = useRouter()

const projectDetailItems = computed(() => [
  { label: 'Service', value: props.project.service },
  { label: 'Responsible Engineer', value: props.project.engineer },
  { label: 'Start Date', value: formatDate(props.project.startDate) },
  { label: 'Target Completion Date', value: formatDate(props.project.targetDate) },
  { label: 'Current Stage', value: props.project.currentStage },
  { label: 'Priority', value: props.project.priority },
])

const clientDetailItems = computed(() => {
  if (!props.client) return []
  return [
    { label: 'Company Name', value: props.client.companyName },
    { label: 'Contact Person', value: props.client.contactPerson },
    { label: 'Mobile', value: props.client.mobile },
    { label: 'Email', value: props.client.email },
    { label: 'City', value: props.client.city },
  ]
})
</script>

<template>
  <div class="flex flex-col gap-6">
    <Card v-if="project.description">
      <template #header>
        <h3 class="text-sm font-semibold text-neutral-800">Scope of Work</h3>
      </template>
      <p class="whitespace-pre-wrap text-sm text-neutral-600">{{ project.description }}</p>
    </Card>

    <div class="grid grid-cols-1 gap-6 laptop:grid-cols-2">
      <DetailPanel title="Project Details" :items="projectDetailItems" />
      <div class="flex flex-col gap-3">
        <DetailPanel title="Client Details" :items="clientDetailItems" />
        <div class="flex gap-2 no-print">
          <BaseButton
            v-if="client"
            variant="secondary"
            size="sm"
            :icon="MessageSquare"
            @click="router.push({ name: ROUTE_NAMES.MESSAGE_CENTRE, query: { clientId: client.id } })"
          >
            Message Client
          </BaseButton>
          <BaseButton
            v-if="client"
            variant="ghost"
            size="sm"
            @click="router.push({ name: ROUTE_NAMES.CLIENT_WORKSPACE, params: { clientId: client.id } })"
          >
            View Full Profile
          </BaseButton>
        </div>
      </div>
    </div>
  </div>
</template>
