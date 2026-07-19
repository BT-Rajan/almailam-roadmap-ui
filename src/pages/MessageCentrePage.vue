<script setup lang="ts">
import { Mail, MessageCircle, Send, Smartphone } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import type { Component } from 'vue'
import { useRoute } from 'vue-router'

import Avatar from '@/components/common/Avatar.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FilterBar from '@/components/common/FilterBar.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SmartTable from '@/components/common/SmartTable.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextArea from '@/components/common/TextArea.vue'
import { useToast } from '@/composables/useToast'
import { useMessageCentreStore } from '@/stores/messageCentreStore'
import type { BadgeVariant } from '@/types/Ui'
import type { SmartTableColumn } from '@/types/Table'
import type { MessageChannel } from '@/types/Message'
import type { SelectOption } from '@/types/Ui'

interface ClientTableRow {
  [key: string]: unknown
  id: string
  companyName: string
  contactPerson: string
  mobile: string
  email: string
  city: string
  status: string
}

interface LogTableRow {
  [key: string]: unknown
  id: string
  companyName: string
  channel: MessageChannel
  templateName: string
  projectName: string
  status: string
  sentAt: string
}

const route = useRoute()
const toast = useToast()
const store = useMessageCentreStore()

const channel = ref<MessageChannel>('Email')
const templateId = ref<string>('')
const messageBody = ref('')
const projectId = ref<string>('')

const CHANNEL_ICONS: Record<MessageChannel, Component> = {
  Email: Mail,
  SMS: Smartphone,
  WhatsApp: MessageCircle,
}

const CHANNEL_BADGE_VARIANT: Record<MessageChannel, BadgeVariant> = {
  Email: 'info',
  SMS: 'warning',
  WhatsApp: 'success',
}

const CHANNEL_OPTIONS: SelectOption[] = [
  { label: 'Email', value: 'Email' },
  { label: 'SMS', value: 'SMS' },
  { label: 'WhatsApp', value: 'WhatsApp' },
]

const CLIENT_COLUMNS: SmartTableColumn<ClientTableRow>[] = [
  { key: 'companyName', label: 'Company', sortable: true },
  { key: 'contactPerson', label: 'Contact Person', sortable: true },
  { key: 'mobile', label: 'Mobile' },
  { key: 'email', label: 'Email' },
  { key: 'city', label: 'City', sortable: true },
  { key: 'status', label: 'Status' },
]

const LOG_COLUMNS: SmartTableColumn<LogTableRow>[] = [
  { key: 'companyName', label: 'Customer', sortable: true },
  { key: 'channel', label: 'Channel' },
  { key: 'templateName', label: 'Template' },
  { key: 'projectName', label: 'Related Project' },
  { key: 'status', label: 'Status' },
  { key: 'sentAt', label: 'Sent', align: 'right' },
]

const clientRows = computed<ClientTableRow[]>(() =>
  store.filteredClients.map((client) => ({
    id: client.id,
    companyName: client.companyName,
    contactPerson: client.contactPerson,
    mobile: client.mobile,
    email: client.email,
    city: client.city,
    status: client.status,
  })),
)

const logRows = computed<LogTableRow[]>(() =>
  store.recentLog.map((entry) => ({
    id: entry.id,
    companyName: store.getClientById(entry.clientId)?.companyName ?? 'Unknown Customer',
    channel: entry.channel,
    templateName: store.templates.find((template) => template.id === entry.templateId)?.name ?? 'Custom message',
    projectName: entry.projectId ? (store.getProjectById(entry.projectId)?.projectName ?? '—') : '—',
    status: entry.status,
    sentAt: new Date(entry.sentAt).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' }),
  })),
)

const templateOptions = computed<SelectOption[]>(() => [
  { label: 'Custom message (no template)', value: '' },
  ...store.templatesForChannel(channel.value).map((template) => ({ label: template.name, value: template.id })),
])

const clientProjectOptions = computed<SelectOption[]>(() => {
  if (!store.selectedClientId) return [{ label: 'No related project', value: '' }]
  return [
    { label: 'No related project', value: '' },
    ...store.getProjectsForClient(store.selectedClientId).map((project) => ({ label: project.projectName, value: project.id })),
  ]
})

const destination = computed(() => {
  if (!store.selectedClient) return ''
  return channel.value === 'Email' ? store.selectedClient.email : store.selectedClient.mobile
})

function resetComposeFields(): void {
  channel.value = 'Email'
  templateId.value = ''
  messageBody.value = ''
  projectId.value = ''
}

function openCompose(row: ClientTableRow): void {
  resetComposeFields()
  store.openCompose(row.id)
}

function closeCompose(): void {
  store.closeCompose()
  resetComposeFields()
}

// Re-apply a template's body (with the contact person's name filled in)
// whenever the template or channel selection changes, but leave the
// field alone if the user already typed something custom for this
// template — switching channel resets template choice, which is the
// signal to also reset the body.
watch(templateId, (newTemplateId) => {
  if (!newTemplateId) return
  const template = store.templates.find((item) => item.id === newTemplateId)
  if (!template || !store.selectedClient) return
  messageBody.value = template.body.split('{contactPerson}').join(store.selectedClient.contactPerson)
})

watch(channel, () => {
  templateId.value = ''
  messageBody.value = ''
})

async function handleSend(): Promise<void> {
  if (!store.selectedClientId || messageBody.value.trim().length === 0) return

  try {
    await store.sendMessage({
      clientId: store.selectedClientId,
      channel: channel.value,
      templateId: templateId.value || undefined,
      body: messageBody.value.trim(),
      projectId: projectId.value || undefined,
    })
    toast.success('Message sent', `${channel.value} sent to ${store.selectedClient?.contactPerson ?? 'customer'}.`)
    closeCompose()
  } catch {
    toast.error('Could not send message', 'Please try again.')
  }
}

function loadData(): void {
  void store.loadAll()
}

onMounted(() => {
  loadData()

  const queryClientId = route.query.clientId
  if (typeof queryClientId === 'string' && queryClientId.length > 0) {
    resetComposeFields()
    store.openCompose(queryClientId)
  }
})
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <PageHeader
      title="Message Centre"
      subtitle="Email, SMS, and WhatsApp communication with your customers — from templates or your own words."
    />

    <FilterBar
      :search-value="store.searchTerm"
      search-placeholder="Search by company, contact, mobile, or email"
      :has-active-filters="store.hasActiveFilters"
      @update:search-value="store.setSearchTerm"
      @clear="store.clearFilters"
    />

    <ErrorState v-if="store.error" :description="store.error" @retry="loadData" />

    <SmartTable
      v-else
      :columns="CLIENT_COLUMNS"
      :rows="clientRows"
      row-key="id"
      :loading="store.isLoading"
      :searchable="false"
      empty-title="No customers found"
      empty-description="Try adjusting your search."
      @row-click="openCompose"
    >
      <template #cell-status="{ value }">
        <StatusBadge :label="value as string" :variant="value === 'Active' ? 'success' : 'neutral'" />
      </template>
      <template #cell-companyName="{ row }">
        <div class="flex items-center gap-2">
          <Avatar :name="(row as ClientTableRow).companyName" size="sm" />
          <span class="font-medium text-neutral-800">{{ (row as ClientTableRow).companyName }}</span>
        </div>
      </template>
    </SmartTable>

    <div>
      <h2 class="mb-3 text-sm font-semibold text-neutral-800">Recent Messages</h2>
      <SmartTable
        :columns="LOG_COLUMNS"
        :rows="logRows"
        row-key="id"
        :searchable="false"
        empty-title="No messages sent yet"
        empty-description="Messages you send will show up here."
      >
        <template #cell-channel="{ value }">
          <StatusBadge :label="value as string" :variant="CHANNEL_BADGE_VARIANT[value as MessageChannel]" show-dot />
        </template>
        <template #cell-status="{ value }">
          <StatusBadge :label="value as string" :variant="value === 'Sent' ? 'success' : 'danger'" />
        </template>
      </SmartTable>
    </div>

    <BaseDrawer v-model="store.isComposeOpen" title="Compose Message" width="lg" @close="closeCompose">
      <div v-if="store.selectedClient" class="flex flex-col gap-5">
        <div class="flex items-center gap-3 rounded-lg border border-border-light bg-bg-secondary p-3">
          <Avatar :name="store.selectedClient.companyName" size="md" />
          <div>
            <p class="text-sm font-semibold text-neutral-800">{{ store.selectedClient.companyName }}</p>
            <p class="text-xs text-neutral-500">{{ store.selectedClient.contactPerson }}</p>
          </div>
        </div>

        <SelectBox :model-value="channel" label="Channel" :options="CHANNEL_OPTIONS" @update:model-value="channel = $event as MessageChannel" />

        <div class="flex items-center gap-2 text-sm text-neutral-600">
          <component :is="CHANNEL_ICONS[channel]" class="h-4 w-4 text-neutral-400" />
          <span>Sending to: <strong class="text-neutral-800">{{ destination }}</strong></span>
        </div>

        <SelectBox v-model="templateId" label="Template" :options="templateOptions" placeholder="Custom message (no template)" />

        <SelectBox v-if="clientProjectOptions.length > 1" v-model="projectId" label="Related Project (optional)" :options="clientProjectOptions" placeholder="No related project" />

        <TextArea v-model="messageBody" label="Message" placeholder="Type your message…" :rows="7" required />
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <BaseButton variant="secondary" @click="closeCompose">Cancel</BaseButton>
          <BaseButton :icon="Send" :loading="store.isSending" :disabled="messageBody.trim().length === 0" @click="handleSend">
            Send {{ channel }}
          </BaseButton>
        </div>
      </template>
    </BaseDrawer>
  </div>
</template>
