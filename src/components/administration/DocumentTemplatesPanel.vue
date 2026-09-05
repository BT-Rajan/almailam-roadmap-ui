<script setup lang="ts">
import { CalendarClock, CheckCircle2, Download, MapPin, Trash2, Upload, UserRound } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import Card from '@/components/common/Card.vue'
import ConfirmationDialog from '@/components/common/ConfirmationDialog.vue'
import IconButton from '@/components/common/IconButton.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import TemplateFieldMapperDialog from '@/components/administration/TemplateFieldMapperDialog.vue'
import { useDocumentTemplateStore } from '@/stores/documentTemplateStore'
import { useToastStore } from '@/stores/toastStore'
import type { AppLanguage } from '@/types/CompanySettings'
import type { DocumentTemplate, DocumentTemplateType } from '@/types/DocumentTemplate'
import type { SelectOption } from '@/types/Ui'
import { formatDate } from '@/utils/dateFormatter'

// Split out of the template below -- a literal '{{' sequence inside a
// Vue mustache interpolation (even nested inside a string literal like
// `{{ '{{ field }}' }}`) trips the SFC template compiler's brace
// matching, so these are plain script constants instead.
const PLACEHOLDER_SYNTAX_EXAMPLE = '{{ field }}'
const ROW_LOOP_SYNTAX_EXAMPLE = '{%tr for ... %}'

const { t } = useI18n()

const LANGUAGES: AppLanguage[] = ['English', 'Arabic']
const LANGUAGE_OPTIONS: SelectOption[] = LANGUAGES.map((language) => ({
  label: language,
  value: language,
  labelKey: language === 'English' ? 'governmentFormOptions.language.english' : 'governmentFormOptions.language.arabic',
}))

const SECTIONS = computed<{ type: DocumentTemplateType; title: string; description: string }[]>(() => [
  {
    type: 'Quotation',
    title: t('administration.documentTemplates.quotationTitle'),
    description: t('administration.documentTemplates.quotationDescription'),
  },
  {
    type: 'Contract',
    title: t('administration.documentTemplates.contractTitle'),
    description: t('administration.documentTemplates.contractDescription'),
  },
])

const store = useDocumentTemplateStore()
const toastStore = useToastStore()

const uploadTarget = ref<DocumentTemplateType | undefined>(undefined)
const uploadLanguage = ref<AppLanguage>('English')
const uploadFile = ref<File>()
const isUploading = ref(false)

const deleteTarget = ref<DocumentTemplate | undefined>(undefined)
const isDeleting = ref(false)
const isSettingDefaultId = ref<string | undefined>(undefined)
const isDownloadingId = ref<string | undefined>(undefined)

const mappingTarget = ref<DocumentTemplate | undefined>(undefined)
const isMapperOpen = ref(false)

function typeLabel(type: DocumentTemplateType): string {
  return type === 'Quotation' ? t('administration.documentTemplates.quotation') : t('administration.documentTemplates.contract')
}

function languageLabel(language: AppLanguage): string {
  return language === 'English' ? t('governmentFormOptions.language.english') : t('governmentFormOptions.language.arabic')
}

function openFieldMapper(template: DocumentTemplate): void {
  mappingTarget.value = template
  isMapperOpen.value = true
}

onMounted(() => {
  if (store.templates.length === 0) store.loadTemplates()
})

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB']
  let size = bytes / 1024
  let index = 0
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024
    index += 1
  }
  return `${size.toFixed(1)} ${units[index]}`
}

function openUpload(type: DocumentTemplateType): void {
  uploadTarget.value = type
  uploadLanguage.value = 'English'
  uploadFile.value = undefined
}

function closeUpload(): void {
  if (isUploading.value) return
  uploadTarget.value = undefined
  uploadFile.value = undefined
}

async function submitUpload(): Promise<void> {
  if (!uploadTarget.value || !uploadFile.value) return
  isUploading.value = true
  try {
    const filename = uploadFile.value.name
    await store.uploadTemplate(uploadTarget.value, uploadLanguage.value, uploadFile.value)
    toastStore.show('success', 'Template uploaded', `${filename} was uploaded.`)
    // Not closeUpload() -- it deliberately no-ops while isUploading is
    // true (so a backdrop click or Cancel can't dismiss mid-upload), and
    // isUploading is still true here; the finally below hasn't run yet.
    uploadTarget.value = undefined
    uploadFile.value = undefined
  } catch (error) {
    toastStore.show('error', 'Upload failed', error instanceof Error ? error.message : 'Please try again.')
  } finally {
    isUploading.value = false
  }
}

async function handleSetDefault(template: DocumentTemplate): Promise<void> {
  isSettingDefaultId.value = template.id
  try {
    await store.setDefaultTemplate(template.id)
    toastStore.show('success', 'Default template updated', `${template.originalFilename} is now the default ${template.documentType} template.`)
  } catch (error) {
    toastStore.show('error', 'Could not set default', error instanceof Error ? error.message : 'Please try again.')
  } finally {
    isSettingDefaultId.value = undefined
  }
}

async function handleDownload(template: DocumentTemplate): Promise<void> {
  isDownloadingId.value = template.id
  try {
    await store.downloadTemplate(template)
  } catch (error) {
    toastStore.show('error', 'Download failed', error instanceof Error ? error.message : 'Please try again.')
  } finally {
    isDownloadingId.value = undefined
  }
}

async function confirmDelete(): Promise<void> {
  if (!deleteTarget.value) return
  isDeleting.value = true
  try {
    await store.deleteTemplate(deleteTarget.value.id)
    toastStore.show('info', 'Template deleted', `${deleteTarget.value.originalFilename} was deleted.`)
    deleteTarget.value = undefined
  } catch (error) {
    toastStore.show('error', 'Delete failed', error instanceof Error ? error.message : 'Please try again.')
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <SkeletonLoader v-if="store.isLoading && store.templates.length === 0" :rows="4" />

    <template v-else>
      <Card v-for="section in SECTIONS" :key="section.type">
        <template #header>
          <div class="flex items-center justify-between gap-3">
            <div>
              <h3 class="text-sm font-semibold text-text-primary">{{ section.title }}</h3>
              <p class="text-xs text-text-muted">{{ section.description }}</p>
            </div>
            <BaseButton size="sm" :icon="Upload" @click="openUpload(section.type)">{{ t('administration.documentTemplates.uploadDocx') }}</BaseButton>
          </div>
        </template>

        <div v-if="store.byType(section.type).length === 0" class="py-4 text-center text-sm text-text-muted">
          {{ t('administration.documentTemplates.noTemplatesForType', { type: typeLabel(section.type) }) }}
        </div>

        <div v-else class="flex flex-col gap-5">
          <div v-for="language in LANGUAGES" :key="language">
            <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-text-muted">{{ languageLabel(language) }}</p>
            <div v-if="store.byTypeAndLanguage(section.type, language).length === 0" class="py-2 text-sm text-text-muted">
              {{ t('administration.documentTemplates.noLanguageTemplates', { language: languageLabel(language), type: typeLabel(section.type) }) }}
            </div>
            <ul v-else class="flex flex-col divide-y divide-border-light">
              <li
                v-for="template in store.byTypeAndLanguage(section.type, language)"
                :key="template.id"
                class="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"
              >
                <div class="flex min-w-0 flex-col gap-1">
                  <div class="flex items-center gap-2">
                    <span class="truncate text-sm font-medium text-text-primary">{{ template.originalFilename }}</span>
                    <StatusBadge v-if="template.isDefault" :label="t('administration.documentTemplates.default')" variant="success" show-dot />
                  </div>
                  <div class="flex items-center gap-3 text-xs text-text-muted">
                    <span class="flex items-center gap-1"><UserRound class="h-3.5 w-3.5" />{{ template.uploadedBy }}</span>
                    <span class="flex items-center gap-1"><CalendarClock class="h-3.5 w-3.5" />{{ formatDate(template.uploadedAt) }}</span>
                    <span>{{ formatFileSize(template.fileSizeBytes) }}</span>
                  </div>
                </div>
                <div class="flex shrink-0 items-center gap-1">
                  <BaseButton
                    v-if="!template.isDefault"
                    variant="secondary"
                    size="sm"
                    :icon="CheckCircle2"
                    :loading="isSettingDefaultId === template.id"
                    @click="handleSetDefault(template)"
                  >
                    {{ t('administration.documentTemplates.setDefault') }}
                  </BaseButton>
                  <IconButton :icon="MapPin" :label="t('administration.documentTemplates.mapFields')" size="sm" @click="openFieldMapper(template)" />
                  <IconButton
                    :icon="Download"
                    :label="t('administration.documentTemplates.downloadTemplate')"
                    size="sm"
                    :disabled="isDownloadingId === template.id"
                    @click="handleDownload(template)"
                  />
                  <IconButton
                    :icon="Trash2"
                    :label="t('administration.documentTemplates.deleteTemplate')"
                    variant="danger"
                    size="sm"
                    :disabled="template.isDefault"
                    @click="deleteTarget = template"
                  />
                </div>
              </li>
            </ul>
          </div>
        </div>
      </Card>
    </template>

    <BaseDialog :model-value="Boolean(uploadTarget)" :title="`Upload ${uploadTarget} Template`" size="sm" :closable="!isUploading" @update:model-value="closeUpload">
      <div class="flex flex-col gap-3">
        <p class="text-xs text-text-muted">
          Word (.docx) only. Any layout works -- once uploaded, use each template's
          <MapPin class="inline h-3 w-3 align-text-bottom" /> "Map fields" button to click merge fields into place
          visually, or hand-type <code class="rounded bg-bg-secondary px-1 py-0.5">{{ PLACEHOLDER_SYNTAX_EXAMPLE }}</code>
          placeholders and, inside a table row, docxtpl's <code class="rounded bg-bg-secondary px-1 py-0.5">{{ ROW_LOOP_SYNTAX_EXAMPLE }}</code>
          row-loop syntax yourself in Word.
        </p>
        <SelectBox
          v-model="uploadLanguage"
          label="Language"
          :options="LANGUAGE_OPTIONS"
          hint="Drives this document's text direction and font when printed/emailed as PDF -- English stays left-to-right, Arabic right-to-left."
        />
        <FileUploader accept=".docx" hint="Word (.docx) template" @select="uploadFile = $event" />
      </div>
      <template #footer>
        <BaseButton variant="secondary" :disabled="isUploading" @click="closeUpload">Cancel</BaseButton>
        <BaseButton :disabled="!uploadFile" :loading="isUploading" @click="submitUpload">Upload</BaseButton>
      </template>
    </BaseDialog>

    <ConfirmationDialog
      :model-value="Boolean(deleteTarget)"
      title="Delete Template"
      :message="`Delete '${deleteTarget?.originalFilename}'? This can't be undone.`"
      confirm-label="Delete"
      confirm-variant="danger"
      :loading="isDeleting"
      @update:model-value="deleteTarget = undefined"
      @confirm="confirmDelete"
    />

    <TemplateFieldMapperDialog v-model="isMapperOpen" :template="mappingTarget" @saved="store.loadTemplates()" />
  </div>
</template>
