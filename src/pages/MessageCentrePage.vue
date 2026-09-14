<script setup lang="ts">
import { Mail, MessageCircle, Paperclip, Send, Smartphone, X } from '@lucide/vue'
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
import TextInput from '@/components/common/TextInput.vue'
import { useToast } from '@/composables/useToast'
import { useMessageCentreStore } from '@/stores/messageCentreStore'
import type { BadgeVariant } from '@/types/Ui'
import type { SmartTableColumn } from '@/types/Table'
import type { MessageChannel } from '@/types/Message'
import type { SelectOption } from '@/types/Ui'
import { formatDateTime } from '@/utils/dateFormatter'
import { getWorkflowStageLabelKey } from '@/utils/projectHelpers'

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
  attachmentCount: number
  status: string
  sentAt: string
}

const route = useRoute()
const { t } = useI18n()
const toast = useToast()
const store = useMessageCentreStore()

const channel = ref<MessageChannel>('Email')
const templateId = ref<string>('')
const subject = ref('')
const messageBody = ref('')
const projectId = ref<string>('')
const attachments = ref<File[]>([])
const fileInput = ref<HTMLInputElement>()

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
  { key: 'attachmentCount', label: t('workspace.messageCentrePage.columnAttachments'), align: 'right' },
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
    templateName: entry.subject || store.templates.find((template) => template.id === entry.templateId)?.name || t('workspace.messageCentrePage.customMessage'),
    projectName: entry.projectId ? (store.getProjectById(entry.projectId)?.projectName ?? '—') : '—',
    attachmentCount: entry.attachments.length,
    status: entry.status,
    sentAt: formatDateTime(entry.sentAt),
  })),
)

const templateOptions = computed<SelectOption[]>(() => [
  { label: t('workspace.messageCentrePage.customMessageNoTemplate'), value: '' },
  ...store.templatesForChannel(channel.value).map((template) => ({ label: template.name, value: template.id })),
])

const clientProjects = computed(() => (store.selectedClientId ? store.getProjectsForClient(store.selectedClientId) : []))

const clientProjectOptions = computed<SelectOption[]>(() => [
  { label: t('workspace.messageCentrePage.noRelatedProject'), value: '' },
  ...clientProjects.value.map((project) => ({ label: project.projectName, value: project.id })),
])

const destination = computed(() => {
  if (!store.selectedClient) return ''
  return channel.value === 'Email' ? store.selectedClient.email : store.selectedClient.mobile
})

const isEmail = computed(() => channel.value === 'Email')

// The whole point of this modal: an Email compose defaults its subject
// to exactly what the recipient needs to place it -- which project,
// and where that project currently stands -- rather than staff typing
// it fresh (or forgetting to) every time. Re-applied whenever the
// selected project changes; staff can still edit it freely afterwards,
// same as the template-body prefill below.
function applyDefaultSubject(): void {
  const project = clientProjects.value.find((p) => p.id === projectId.value)
  subject.value = project ? `${project.projectName} - ${t(getWorkflowStageLabelKey(project.currentStage))}` : ''
}

watch(projectId, () => {
  if (isEmail.value) applyDefaultSubject()
})

function resetComposeFields(): void {
  channel.value = 'Email'
  templateId.value = ''
  subject.value = ''
  messageBody.value = ''
  projectId.value = ''
  attachments.value = []
}

function openCompose(row: ClientTableRow): void {
  resetComposeFields()
  store.openCompose(row.id)
  // A customer with exactly one project has an unambiguous answer to
  // "which project is this email about" -- pick it automatically so
  // the subject line is already filled in when the modal opens,
  // instead of making staff pick from a list of one.
  const projects = store.getProjectsForClient(row.id)
  if (projects.length === 1) {
    projectId.value = projects[0].id
    applyDefaultSubject()
  }
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
  attachments.value = []
  if (isEmail.value) {
    applyDefaultSubject()
  } else {
    subject.value = ''
  }
})

function triggerFilePicker(): void {
  fileInput.value?.click()
}

function handleFilesSelected(event: Event): void {
  const input = event.target as HTMLInputElement
  attachments.value = [...attachments.value, ...Array.from(input.files ?? [])]
  input.value = ''
}

function removeAttachment(index: number): void {
  attachments.value = attachments.value.filter((_, i) => i !== index)
}

const canSend = computed(() => {
  if (messageBody.value.trim().length === 0) return false
  if (isEmail.value && subject.value.trim().length === 0) return false
  return true
})

async function handleSend(): Promise<void> {
  if (!store.selectedClientId || !canSend.value) return

  try {
    if (isEmail.value) {
      await store.sendEmail({
        clientId: store.selectedClientId,
        subject: subject.value.trim(),
        body: messageBody.value.trim(),
        projectId: projectId.value || undefined,
        files: attachments.value,
      })
    } else {
      await store.sendMessage({
        clientId: store.selectedClientId,
        channel: channel.value,
        templateId: templateId.value || undefined,
        body: messageBody.value.trim(),
        projectId: projectId.value || undefined,
      })
    }
    toast.success(
      t('workspace.messageCentrePage.messageSentTitle'),
      t('workspace.messageCentrePage.messageSentDescription', {
        channel: channel.value,
        name: store.selectedClient?.contactPerson ?? t('workspace.messageCentrePage.unknownCustomerFallback'),
      }),
    )
    closeCompose()
  } catch (error) {
    toast.error(
      t('workspace.messageCentrePage.couldNotSendMessageTitle'),
      error instanceof Error ? error.message : t('common.pleaseTryAgain'),
    )
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
    const projects = store.getProjectsForClient(queryClientId)
    if (projects.length === 1) {
      projectId.value = projects[0].id
      applyDefaultSubject()
    }
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
        <template #cell-attachmentCount="{ value }">
          <span v-if="(value as number) > 0" class="inline-flex items-center gap-1 text-xs text-text-muted">
            <Paperclip class="h-3.5 w-3.5" />
            {{ value }}
          </span>
          <span v-else class="text-xs text-text-muted">—</span>
        </template>
        <template #cell-status="{ value }">
          <StatusBadge :label="value as string" :variant="value === 'Sent' ? 'success' : 'danger'" />
        </template>
      </SmartTable>
    </div>

    <BaseDrawer v-model="store.isComposeOpen" :title="isEmail ? t('workspace.messageCentrePage.composeEmailTitle') : t('workspace.messageCentrePage.composeMessage')" width="lg" @close="closeCompose">
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
          <span>{{ t('workspace.messageCentrePage.sendingTo') }} <strong class="text-text-primary">{{ destination || '—' }}</strong></span>
        </div>
        <p v-if="isEmail && !destination" class="-mt-3 text-xs text-danger-500">{{ t('workspace.messageCentrePage.noEmailOnFile') }}</p>

        <SelectBox v-if="clientProjectOptions.length > 1" v-model="projectId" :label="t('workspace.messageCentrePage.relatedProjectOptional')" :options="clientProjectOptions" :placeholder="t('workspace.messageCentrePage.noRelatedProject')" />

        <TextInput v-if="isEmail" v-model="subject" :label="t('workspace.messageCentrePage.subject')" :placeholder="t('workspace.messageCentrePage.subjectPlaceholder')" required />

        <SelectBox v-model="templateId" :label="t('workspace.messageCentrePage.template')" :options="templateOptions" :placeholder="t('workspace.messageCentrePage.customMessageNoTemplate')" />

        <TextArea v-model="messageBody" :label="t('workspace.messageCentrePage.message')" :placeholder="t('workspace.messageCentrePage.messagePlaceholder')" :rows="7" required />

        <div v-if="isEmail" class="flex flex-col gap-2">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-text-primary">{{ t('workspace.messageCentrePage.attachments') }}</span>
            <BaseButton variant="secondary" size="sm" :icon="Paperclip" @click="triggerFilePicker">
              {{ t('workspace.messageCentrePage.addAttachment') }}
            </BaseButton>
          </div>
          <input ref="fileInput" type="file" multiple class="hidden" @change="handleFilesSelected" />
          <p v-if="attachments.length === 0" class="text-xs text-text-muted">{{ t('workspace.messageCentrePage.noAttachmentsAdded') }}</p>
          <ul v-else class="flex flex-col gap-1.5">
            <li
              v-for="(file, index) in attachments"
              :key="`${file.name}-${index}`"
              class="flex items-center justify-between gap-2 rounded-md border border-border-light bg-bg-secondary px-3 py-1.5 text-sm"
            >
              <span class="flex min-w-0 items-center gap-2 truncate text-text-primary">
                <Paperclip class="h-3.5 w-3.5 shrink-0 text-text-muted" />
                <span class="truncate">{{ file.name }}</span>
              </span>
              <button
                type="button"
                class="shrink-0 rounded p-0.5 text-text-muted transition-colors hover:bg-bg-tertiary hover:text-danger-500"
                :aria-label="t('workspace.messageCentrePage.removeAttachment', { name: file.name })"
                @click="removeAttachment(index)"
              >
                <X class="h-3.5 w-3.5" />
              </button>
            </li>
          </ul>
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end gap-3">
          <BaseButton variant="secondary" @click="closeCompose">{{ t('common.cancel') }}</BaseButton>
          <BaseButton :icon="Send" :loading="store.isSending" :disabled="!canSend" @click="handleSend">
            {{ t('workspace.messageCentrePage.send', { channel }) }}
          </BaseButton>
        </div>
      </template>
    </BaseDrawer>
  </div>
</template>
