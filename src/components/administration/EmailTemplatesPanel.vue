<script setup lang="ts">
import { Copy, Mail } from '@lucide/vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { emailTemplateService } from '@/services/emailTemplateService'
import { useEmailTemplateStore } from '@/stores/emailTemplateStore'
import { useToastStore } from '@/stores/toastStore'
import type { EmailMergeField, EmailTemplateKey } from '@/types/EmailTemplate'
import { formatDateTime } from '@/utils/dateFormatter'

// The chip's literal '{{ ... }}' text is written as a plain script
// constant, not inline in the template below -- a literal '{{'
// sequence inside a Vue mustache trips the SFC template compiler's
// brace matching (see DocumentTemplatesPanel.vue's own note).
function tokenFor(fieldKey: string): string {
  return '{{ ' + fieldKey + ' }}'
}

const { t } = useI18n()
const emailTemplateStore = useEmailTemplateStore()
const toastStore = useToastStore()

// Fixed display order/copy for the 7 keys -- purely presentational
// (friendly name + "when this sends"), not a second source of truth
// for which keys exist (that's EMAIL_TEMPLATE_KEYS on the backend).
const TEMPLATE_INFO: { key: EmailTemplateKey; labelKey: string; descriptionKey: string }[] = [
  { key: 'client_onboarding_otp', labelKey: 'administration.emailTemplates.keys.clientOnboardingOtp.label', descriptionKey: 'administration.emailTemplates.keys.clientOnboardingOtp.description' },
  { key: 'client_welcome', labelKey: 'administration.emailTemplates.keys.clientWelcome.label', descriptionKey: 'administration.emailTemplates.keys.clientWelcome.description' },
  { key: 'project_created', labelKey: 'administration.emailTemplates.keys.projectCreated.label', descriptionKey: 'administration.emailTemplates.keys.projectCreated.description' },
  { key: 'requirement_otp', labelKey: 'administration.emailTemplates.keys.requirementOtp.label', descriptionKey: 'administration.emailTemplates.keys.requirementOtp.description' },
  { key: 'requirement_confirmed', labelKey: 'administration.emailTemplates.keys.requirementConfirmed.label', descriptionKey: 'administration.emailTemplates.keys.requirementConfirmed.description' },
  { key: 'quotation_otp', labelKey: 'administration.emailTemplates.keys.quotationOtp.label', descriptionKey: 'administration.emailTemplates.keys.quotationOtp.description' },
  { key: 'quotation_approved', labelKey: 'administration.emailTemplates.keys.quotationApproved.label', descriptionKey: 'administration.emailTemplates.keys.quotationApproved.description' },
  { key: 'contract_otp', labelKey: 'administration.emailTemplates.keys.contractOtp.label', descriptionKey: 'administration.emailTemplates.keys.contractOtp.description' },
  { key: 'contract_signed', labelKey: 'administration.emailTemplates.keys.contractSigned.label', descriptionKey: 'administration.emailTemplates.keys.contractSigned.description' },
]

const selectedKey = ref<EmailTemplateKey>()
const mergeFields = ref<EmailMergeField[]>([])
const isLoadingFields = ref(false)

const form = reactive({ subject: '', body: '' })
const isSaving = ref(false)

const selectedTemplate = computed(() => (selectedKey.value ? emailTemplateStore.byKey(selectedKey.value) : undefined))
const hasChanges = computed(
  () => Boolean(selectedTemplate.value) && (form.subject !== selectedTemplate.value?.subject || form.body !== selectedTemplate.value?.body),
)

async function selectTemplate(key: EmailTemplateKey): Promise<void> {
  selectedKey.value = key
  const template = emailTemplateStore.byKey(key)
  form.subject = template?.subject ?? ''
  form.body = template?.body ?? ''
  isLoadingFields.value = true
  try {
    mergeFields.value = await emailTemplateService.getMergeFields(key)
  } catch {
    // Called directly from a template @click with no .catch of its own --
    // if the backend that just failed to load the template list also
    // can't serve merge fields, leaving this unhandled would surface as
    // a console rejection with no visible effect, which is worse than
    // just leaving the reference list empty.
    mergeFields.value = []
  } finally {
    isLoadingFields.value = false
  }
}

async function loadData(): Promise<void> {
  await emailTemplateStore.loadTemplates()
  if (emailTemplateStore.templates.length > 0) void selectTemplate(emailTemplateStore.templates[0].key)
}

onMounted(loadData)

// Re-seeds the form if the underlying store data changes out from under
// the currently-open template (e.g. a save from elsewhere) -- doesn't
// fire from this panel's own save, which updates selectedKey's identity
// via the store itself so this stays in sync either way.
watch(selectedTemplate, (template) => {
  if (!template || hasChanges.value) return
  form.subject = template.subject
  form.body = template.body
})

async function copyToken(fieldKey: string): Promise<void> {
  await navigator.clipboard.writeText(tokenFor(fieldKey))
  toastStore.show('success', t('administration.emailTemplates.tokenCopiedTitle'), tokenFor(fieldKey))
}

async function handleSave(): Promise<void> {
  if (!selectedKey.value) return
  isSaving.value = true
  try {
    await emailTemplateStore.updateTemplate(selectedKey.value, form.subject, form.body)
    toastStore.show('success', t('administration.emailTemplates.savedTitle'), t('administration.emailTemplates.savedDescription'))
  } catch (error) {
    toastStore.show('error', t('administration.emailTemplates.failedToSave'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isSaving.value = false
  }
}

function handleCancel(): void {
  if (!selectedTemplate.value) return
  form.subject = selectedTemplate.value.subject
  form.body = selectedTemplate.value.body
}
</script>

<template>
  <div class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
    <div class="flex flex-col gap-2 laptop:col-span-1">
      <SkeletonLoader v-if="emailTemplateStore.isLoading" :rows="TEMPLATE_INFO.length" />
      <button
        v-for="info in TEMPLATE_INFO"
        :key="info.key"
        type="button"
        class="flex flex-col gap-0.5 rounded-lg border px-3 py-2.5 text-start transition-colors duration-fast"
        :class="
          selectedKey === info.key
            ? 'border-accent-500 bg-accent-50 dark:bg-accent-500/10'
            : 'border-border-light hover:border-accent-300'
        "
        @click="selectTemplate(info.key)"
      >
        <span class="text-sm font-medium text-text-primary">{{ t(info.labelKey) }}</span>
        <span class="text-xs text-text-muted">{{ t(info.descriptionKey) }}</span>
      </button>
    </div>

    <div class="laptop:col-span-2">
      <ErrorState
        v-if="emailTemplateStore.error && emailTemplateStore.templates.length === 0"
        :description="emailTemplateStore.error"
        @retry="loadData"
      />
      <EmptyState
        v-else-if="!selectedTemplate && !emailTemplateStore.isLoading"
        :icon="Mail"
        :title="t('administration.emailTemplates.emptyTitle')"
        :description="t('administration.emailTemplates.emptyDescription')"
      />
      <Card v-else-if="selectedTemplate">
        <div class="flex flex-col gap-4">
          <p class="text-xs text-text-muted">
            {{ t('administration.emailTemplates.lastUpdated', { by: selectedTemplate.updatedBy, at: formatDateTime(selectedTemplate.updatedAt) }) }}
          </p>

          <TextInput v-model="form.subject" :label="t('administration.emailTemplates.subjectLabel')" required />
          <TextArea v-model="form.body" :label="t('administration.emailTemplates.bodyLabel')" :rows="12" required />

          <div class="flex flex-col gap-2 rounded-lg border border-border-light bg-bg-secondary p-3">
            <span class="text-xs font-medium text-text-secondary">{{ t('administration.emailTemplates.availableFields') }}</span>
            <SkeletonLoader v-if="isLoadingFields" :rows="2" />
            <div v-else class="flex flex-wrap gap-2">
              <button
                v-for="field in mergeFields"
                :key="field.key"
                type="button"
                class="inline-flex items-center gap-1 rounded-full border border-accent-300 bg-accent-100 px-2.5 py-1 text-xs font-medium text-accent-700 transition-colors duration-fast hover:bg-accent-200"
                :title="field.label"
                @click="copyToken(field.key)"
              >
                <Copy class="h-3 w-3 shrink-0" />
                {{ field.label }}
              </button>
            </div>
          </div>

          <FormActionBar :loading="isSaving" :disabled="!hasChanges" @submit="handleSave" @cancel="handleCancel" />
        </div>
      </Card>
    </div>
  </div>
</template>
