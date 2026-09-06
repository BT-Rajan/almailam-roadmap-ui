<script setup lang="ts">
import { CheckCircle2, Plug, XCircle } from '@lucide/vue'
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

import ErrorState from '@/components/common/ErrorState.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import FormSection from '@/components/common/FormSection.vue'
import BaseButton from '@/components/common/BaseButton.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextInput from '@/components/common/TextInput.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import { useEmailSettingsStore } from '@/stores/emailSettingsStore'
import { useToastStore } from '@/stores/toastStore'
import type { EmailProviderId } from '@/types/EmailSettings'
import type { SelectOption } from '@/types/Ui'
import { formatDateTime } from '@/utils/dateFormatter'

const { t } = useI18n()
const emailSettingsStore = useEmailSettingsStore()
const toastStore = useToastStore()

const providerOptions = computed<SelectOption[]>(() =>
  Object.entries(emailSettingsStore.presets ?? {}).map(([id, preset]) => ({ label: preset.label, value: id })),
)

const providerNote = computed(() => {
  if (!emailSettingsStore.settings || !emailSettingsStore.presets) return ''
  return emailSettingsStore.presets[emailSettingsStore.settings.provider]?.note ?? ''
})

// Gmail/Outlook/Yahoo/iCloud's host, port, and encryption are fixed,
// published values -- letting them drift from the real setting (a typo,
// an accidental edit) is a common cause of "the password is right but
// it still won't connect". Only "custom" leaves them editable.
const isCustomProvider = computed(() => emailSettingsStore.settings?.provider === 'custom')

function loadData(): void {
  emailSettingsStore.loadSettings()
}

onMounted(() => {
  if (!emailSettingsStore.settings) loadData()
})

async function handleSave(): Promise<void> {
  const success = await emailSettingsStore.saveSettings()
  if (success) {
    toastStore.show('success', t('administration.emailPage.settingsSaved'), t('administration.emailPage.settingsSavedHint'))
  } else {
    toastStore.show('error', t('administration.emailPage.unableToSave'), emailSettingsStore.error ?? t('administration.emailPage.pleaseTryAgain'))
  }
}

function handleCancel(): void {
  loadData()
}

async function handleTest(): Promise<void> {
  // Test Connection validates whatever is saved in the database, not
  // whatever happens to be typed in the form right now -- so without
  // saving first, a password (or any other field) just typed in looks
  // identical to nothing being set at all, which reads as a confusing
  // false failure. Save immediately before testing so the two can
  // never disagree.
  const saved = await emailSettingsStore.saveSettings()
  if (!saved) {
    toastStore.show('error', t('administration.emailPage.unableToSave'), emailSettingsStore.error ?? t('administration.emailPage.pleaseTryAgain'))
    return
  }
  const result = await emailSettingsStore.testConnection()
  toastStore.show(
    result.ok ? 'success' : 'error',
    result.ok ? t('administration.emailPage.connectionSuccessful') : t('administration.emailPage.connectionFailed'),
    result.message,
  )
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader :title="t('administration.emailPage.pageTitle')" :subtitle="t('administration.emailPage.pageSubtitle')" />

    <ErrorState v-if="emailSettingsStore.error && !emailSettingsStore.settings" :description="emailSettingsStore.error" @retry="loadData" />

    <div v-else-if="emailSettingsStore.isLoading || !emailSettingsStore.settings" class="rounded-xl border border-border-light bg-bg-card p-6">
      <SkeletonLoader :rows="10" />
    </div>

    <div v-else class="flex max-w-3xl flex-col gap-8 rounded-xl border border-border-light bg-bg-card p-6">
      <div
        v-if="emailSettingsStore.settings.envOverrideActive"
        class="flex items-start gap-2 rounded-lg border border-warning-200 bg-warning-50 p-3 text-sm text-warning-700"
      >
        <span>{{ t('administration.emailPage.envOverrideNotice') }}</span>
      </div>

      <FormSection :title="t('administration.emailPage.mailbox')" :description="t('administration.emailPage.mailboxDescription')">
        <ToggleSwitch
          :model-value="emailSettingsStore.settings.isActive"
          :label="t('administration.emailPage.enableMailbox')"
          :hint="t('administration.emailPage.enableMailboxHint')"
          @update:model-value="emailSettingsStore.updateField('isActive', $event)"
        />

        <SelectBox
          :model-value="emailSettingsStore.settings.provider"
          :label="t('administration.emailPage.provider')"
          :options="providerOptions"
          @update:model-value="emailSettingsStore.applyProviderPreset($event as EmailProviderId)"
        />
        <p v-if="providerNote" class="-mt-2 text-xs text-text-muted">{{ providerNote }}</p>

        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput
            :model-value="emailSettingsStore.settings.smtpHost"
            :label="t('administration.emailPage.smtpHost')"
            :disabled="!isCustomProvider"
            @update:model-value="emailSettingsStore.updateField('smtpHost', $event)"
          />
          <NumberInput
            :model-value="emailSettingsStore.settings.smtpPort"
            :label="t('administration.emailPage.smtpPort')"
            :min="1"
            :max="65535"
            :disabled="!isCustomProvider"
            @update:model-value="emailSettingsStore.updateField('smtpPort', Number($event))"
          />
        </div>

        <ToggleSwitch
          :model-value="emailSettingsStore.settings.smtpUseTls"
          :label="t('administration.emailPage.useTls')"
          :hint="isCustomProvider ? t('administration.emailPage.useTlsHint') : t('administration.emailPage.useTlsLockedHint')"
          :disabled="!isCustomProvider"
          @update:model-value="emailSettingsStore.updateField('smtpUseTls', $event)"
        />

        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput
            :model-value="emailSettingsStore.settings.username"
            :label="t('administration.emailPage.username')"
            :placeholder="t('administration.emailPage.usernamePlaceholder')"
            @update:model-value="emailSettingsStore.updateField('username', $event)"
          />
          <TextInput
            :model-value="emailSettingsStore.settings.password ?? ''"
            type="password"
            show-password-toggle
            :label="emailSettingsStore.settings.hasPassword ? t('administration.emailPage.passwordSaved') : t('administration.emailPage.password')"
            :placeholder="t('administration.emailPage.passwordPlaceholder')"
            @update:model-value="emailSettingsStore.updatePassword($event)"
          />
        </div>

        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput
            :model-value="emailSettingsStore.settings.fromEmail"
            type="email"
            :label="t('administration.emailPage.fromEmail')"
            @update:model-value="emailSettingsStore.updateField('fromEmail', $event)"
          />
          <TextInput
            :model-value="emailSettingsStore.settings.fromName"
            :label="t('administration.emailPage.fromName')"
            @update:model-value="emailSettingsStore.updateField('fromName', $event)"
          />
        </div>
      </FormSection>

      <FormSection :title="t('administration.emailPage.connection')" :description="t('administration.emailPage.connectionDescription')">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-2">
            <StatusBadge
              v-if="emailSettingsStore.settings.lastTestOk !== null"
              :label="emailSettingsStore.settings.lastTestOk ? t('administration.emailPage.connected') : t('administration.emailPage.notConnected')"
              :variant="emailSettingsStore.settings.lastTestOk ? 'success' : 'danger'"
              show-dot
            />
            <span v-if="emailSettingsStore.settings.lastTestedAt" class="text-xs text-text-muted">
              {{ t('administration.emailPage.lastTested', { time: formatDateTime(emailSettingsStore.settings.lastTestedAt) }) }}
            </span>
          </div>
          <BaseButton
            variant="ghost"
            size="sm"
            :icon="Plug"
            :loading="emailSettingsStore.isSaving || emailSettingsStore.isTesting"
            @click="handleTest"
          >
            {{ t('administration.emailPage.testConnection') }}
          </BaseButton>
        </div>
        <p
          v-if="emailSettingsStore.settings.lastTestError"
          class="flex items-center gap-1.5 text-xs text-danger-600"
        >
          <XCircle class="h-3.5 w-3.5 shrink-0" />
          {{ emailSettingsStore.settings.lastTestError }}
        </p>
        <p v-else-if="emailSettingsStore.settings.lastTestOk" class="flex items-center gap-1.5 text-xs text-success-600">
          <CheckCircle2 class="h-3.5 w-3.5 shrink-0" />
          {{ t('administration.emailPage.testResultOk') }}
        </p>
      </FormSection>

      <FormActionBar :submit-label="t('administration.emailPage.saveChanges')" :loading="emailSettingsStore.isSaving" @submit="handleSave" @cancel="handleCancel" />
    </div>
  </div>
</template>
