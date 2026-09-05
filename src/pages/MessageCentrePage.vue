<script setup lang="ts">
import { Mail, MessageCircle, Send, Smartphone } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import type { Component } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import Avatar from '@/components/common/Avatar.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import ErrorState from '@/components/common/ErrorState.vue'
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
const { t } = useI18n()
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

const CLIENT_COLUMNS = computed<SmartTableColumn<ClientTableRow>[]>(() => [
  { key: 'companyName', label: t('workspace.messageCentrePage.columnCompany'), sortable: true },
  { key: 'contactPerson', label: t('workspace.messageCentrePage.columnContactPerson'), sortable: true },
  { key: 'mobile', label: t('workspace.messageCentrePage.columnMobile') },
  { key: 'email', label: t('workspace.messageCentrePage.columnEmail') },
  { key: 'city', label: t('workspace.messageCentrePage.columnCity'), sortable: true },
  { key: 'status', label: t('workspace.messageCentrePage.columnStatus') },
])

const LOG_COLUMNS = computed<SmartTableColumn<LogTableRow>[]>(() => [
  { key: 'companyName', label: t('workspace.messageCentrePage.columnCustomer'), sortable: true },
  { key: 'channel', label: t('workspace.messageCentrePage.columnChannel') },
  { key: 'templateName', label: t('workspace.messageCentrePage.columnTemplate') },
  { key: 'projectName', label: t('workspace.messageCentrePage.columnRelatedProject') },
  { key: 'status', label: t('workspace.messageCentrePage.columnStatus') },
  { key: 'sentAt', label: t('workspace.messageCentrePage.columnSent'), align: 'right' },
])

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
    companyName: store.getClientById(entry.clientId)?.companyName ?? t('workspace.messageCentrePage.unknownCustomer'),
    channel: entry.channel,
    templateName: store.templates.find((template) => template.id === entry.templateId)?.name ?? t('workspace.messageCentrePage.customMessage'),
    projectName: entry.projectId ? (store.getProjectById(entry.projectId)?.projectName ?? '—') : '—',
    status: entry.status,
    sentAt: new Date(entry.sentAt).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' }),
  })),
)

const templateOptions = computed<SelectOption[]>(() => [
  { label: t('workspace.messageCentrePage.customMessageNoTemplate'), value: '' },
  ...store.templatesForChannel(channel.value).map((template) => ({ label: template.name, value: template.id })),
])

const clientProjectOptions = computed<SelectOption[]>(() => {
  if (!store.selectedClientId) return [{ label: t('workspace.messageCentrePage.noRelatedProject'), value: '' }]
  return [
    { label: t('workspace.messageCentrePage.noRelatedProject'), value: '' },
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
      :title="t('workspace.messageCentrePage.pageTitle')"
      :subtitle="t('workspace.messageCentrePage.pageSubtitle')"
    />

    <ErrorState v-if="store.error" :description="store.error" @retry="loadData" />

    <SmartTable
      v-else
      :columns="CLIENT_COLUMNS"
      :rows="clientRows"
      row-key="id"
      :loading="store.isLoading"
      :searchable="false"
      :empty-title="t('workspace.messageCentrePage.noCustomersFound')"
      :empty-description="t('workspace.messageCentrePage.noCustomersFoundDescription')"
      @row-click="openCompose"
    >
      <template #cell-status="{ value }">
        <StatusBadge :label="value as string" :variant="value === 'Active' ? 'success' : 'neutral'" />
      </template>
      <template #cell-companyName="{ row }">
        <div class="flex items-center gap-2">
          <Avatar :name="(row as ClientTableRow).companyName" size="sm" />
          <span class="font-medium text-text-primary">{{ (row as ClientTableRow).companyName }}</span>
        </div>
      </template>
    </SmartTable>

    <div>
      <h2 class="mb-3 text-sm font-semibold text-text-primary">{{ t('workspace.messageCentrePage.recentMessages') }}</h2>
      <SmartTable
        :columns="LOG_COLUMNS"
        :rows="logRows"
        row-key="id"
        :searchable="false"
        :empty-title="t('workspace.messageCentrePage.noMessagesSentYet')"
        :empty-description="t('workspace.messageCentrePage.noMessagesSentYetDescription')"
      >
        <template #cell-channel="{ value }">
          <StatusBadge :label="value as string" :variant="CHANNEL_BADGE_VARIANT[value as MessageChannel]" show-dot />
        </template>
        <template #cell-status="{ value }">
          <StatusBadge :label="value as string" :variant="value === 'Sent' ? 'success' : 'danger'" />
        </template>
      </SmartTable>
    </div>

    <BaseDrawer v-model="store.isComposeOpen" :title="t('workspace.messageCentrePage.composeMessage')" width="lg" @close="closeCompose">
      <div v-if="store.selectedClient" class="flex flex-col gap-5">
        <div class="flex items-center gap-3 rounded-lg border border-border-light bg-bg-secondary p-3">
          <Avatar :name="store.selectedClient.companyName" size="md" />
          <div>
            <p class="text-sm font-semibold text-text-primary">{{ store.selectedClient.companyName }}</p>
            <p class="text-xs text-text-muted">{{ store.selectedClient.contactPerson }}</p>
          </div>
        </div>

        <SelectBox :model-value="channel" :label="t('workspace.messageCentrePage.channel')" :options="CHANNEL_OPTIONS" @update:model-value="channel = $event as MessageChannel" />

        <div class="flex items-center gap-2 text-sm text-text-secondary">
          <component :is="CHANNEL_ICONS[channel]" class="h-4 w-4 text-text-muted" />
          <span>{{ t('workspace.messageCentrePage.sendingTo') }} <strong class="text-text-primary">{{ destination }}</strong></span>
        </div>

        <SelectBox v-model="templateId" :label="t('workspace.messageCentrePage.template')" :options="templateOptions" :placeholder="t('workspace.messageCentrePage.customMessageNoTemplate')" />

        <SelectBox v-if="clientProjectOptions.length > 1" v-model="projectId" :label="t('workspace.messageCentrePage.relatedProjectOptional')" :options="clientProjectOptions" :placeholder="t('workspace.messageCentrePage.noRelatedProject')" />

        <TextArea v-model="messageBody" :label="t('workspace.messageCentrePage.message')" :placeholder="t('workspace.messageCentrePage.messagePlaceholder')" :rows="7" required />
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <BaseButton variant="secondary" @click="closeCompose">{{ t('common.cancel') }}</BaseButton>
          <BaseButton :icon="Send" :loading="store.isSending" :disabled="messageBody.trim().length === 0" @click="handleSend">
            {{ t('workspace.messageCentrePage.send', { channel }) }}
          </BaseButton>
        </div>
      </template>
    </BaseDrawer>
  </div>
</template>
