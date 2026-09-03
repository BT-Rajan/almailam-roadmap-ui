<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import FormSection from '@/components/common/FormSection.vue'
import NumberInput from '@/components/common/NumberInput.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextInput from '@/components/common/TextInput.vue'
import FileUploader from '@/components/document/FileUploader.vue'
import CompanyProfileCard from '@/components/administration/CompanyProfileCard.vue'
import { companyService } from '@/services/companyService'
import { useCompanyStore } from '@/stores/companyStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import type { AppLanguage } from '@/types/CompanySettings'
import type { SelectOption } from '@/types/Ui'

const companyStore = useCompanyStore()
const toastStore = useToastStore()
const userStore = useUserStore()

// Object URL for the logo preview <img> -- fetched as a Blob (the
// endpoint needs an Authorization header a plain <img src> can't send),
// so this is built/torn down by hand rather than pointing straight at
// the API.
const logoPreviewUrl = ref<string | undefined>(undefined)
const isUploadingLogo = ref(false)
const isRemovingLogo = ref(false)

function clearLogoPreview(): void {
  if (logoPreviewUrl.value) URL.revokeObjectURL(logoPreviewUrl.value)
  logoPreviewUrl.value = undefined
}

async function refreshLogoPreview(): Promise<void> {
  clearLogoPreview()
  if (!companyStore.settings?.hasLogo) return
  try {
    const blob = await companyService.getLogoBlob()
    logoPreviewUrl.value = URL.createObjectURL(blob)
  } catch {
    // Preview is a nice-to-have -- the rest of the page still works
    // (upload/remove buttons, filename text) if this fails.
  }
}

watch(() => companyStore.settings?.hasLogo, refreshLogoPreview)
onUnmounted(clearLogoPreview)

async function handleLogoSelect(file: File | undefined): Promise<void> {
  if (!file) return
  isUploadingLogo.value = true
  try {
    await companyStore.uploadLogo(file)
    toastStore.show('success', 'Logo updated', 'The company logo is now available to insert in document templates.')
  } catch (error) {
    toastStore.show('error', 'Failed to upload logo', error instanceof Error ? error.message : 'Please try again.')
  } finally {
    isUploadingLogo.value = false
  }
}

async function handleLogoRemove(): Promise<void> {
  isRemovingLogo.value = true
  try {
    await companyStore.deleteLogo()
    toastStore.show('info', 'Logo removed')
  } catch (error) {
    toastStore.show('error', 'Failed to remove logo', error instanceof Error ? error.message : 'Please try again.')
  } finally {
    isRemovingLogo.value = false
  }
}

const statusReportRecipientOptions = computed<SelectOption[]>(() =>
  userStore.users.filter((user) => user.status === 'Active').map((user) => ({ label: `${user.name} (${user.role})`, value: user.id })),
)

const LANGUAGE_OPTIONS: SelectOption[] = [
  { label: 'English', value: 'English' },
  { label: 'Arabic', value: 'Arabic' },
]

const DATE_FORMAT_OPTIONS: SelectOption[] = [
  { label: 'DD/MM/YYYY', value: 'DD/MM/YYYY' },
  { label: 'MM/DD/YYYY', value: 'MM/DD/YYYY' },
  { label: 'YYYY-MM-DD', value: 'YYYY-MM-DD' },
]

const CURRENCY_OPTIONS: SelectOption[] = [
  { label: 'AED - UAE Dirham', value: 'AED' },
  { label: 'USD - US Dollar', value: 'USD' },
  { label: 'SAR - Saudi Riyal', value: 'SAR' },
  { label: 'KWD - Kuwaiti Dinar', value: 'KWD' },
]

function loadData(): void {
  companyStore.loadSettings()
}

onMounted(() => {
  if (!companyStore.settings) loadData()
  if (userStore.users.length === 0) userStore.loadUsers()
})

async function handleSave(): Promise<void> {
  const success = await companyStore.saveSettings()
  if (success) {
    toastStore.show('success', 'Company settings saved', 'Your changes have been applied.')
  }
}

function handleCancel(): void {
  loadData()
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader title="Company Settings" subtitle="Manage your company profile, branding and business preferences." />

    <ErrorState v-if="companyStore.error" :description="companyStore.error" @retry="loadData" />

    <div v-else-if="companyStore.isLoading" class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="rounded-xl border border-border-light bg-bg-card p-6">
        <SkeletonLoader :rows="6" />
      </div>
      <div class="rounded-xl border border-border-light bg-bg-card p-6 laptop:col-span-2">
        <SkeletonLoader :rows="10" />
      </div>
    </div>

    <div v-else-if="companyStore.settings" class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <CompanyProfileCard :settings="companyStore.settings" />

      <div class="flex flex-col gap-8 rounded-xl border border-border-light bg-bg-card p-6 laptop:col-span-2">
        <FormSection title="Company Profile" description="Basic details shown on quotations, contracts and government submissions.">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <TextInput
              :model-value="companyStore.settings.companyName"
              label="Company Name"
              required
              @update:model-value="companyStore.updateField('companyName', $event)"
            />
            <TextInput
              :model-value="companyStore.settings.tagline"
              label="Tagline"
              @update:model-value="companyStore.updateField('tagline', $event)"
            />
            <TextInput
              :model-value="companyStore.settings.tradeLicenseNumber"
              label="Trade License Number"
              @update:model-value="companyStore.updateField('tradeLicenseNumber', $event)"
            />
            <TextInput
              :model-value="companyStore.settings.website"
              label="Website"
              @update:model-value="companyStore.updateField('website', $event)"
            />
            <TextInput
              :model-value="companyStore.settings.email"
              type="email"
              label="Email"
              @update:model-value="companyStore.updateField('email', $event)"
            />
            <TextInput
              :model-value="companyStore.settings.phone"
              type="tel"
              label="Phone"
              @update:model-value="companyStore.updateField('phone', $event)"
            />
          </div>
        </FormSection>

        <FormSection title="Address" description="Registered office address used on official documents.">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <TextInput
              :model-value="companyStore.settings.address"
              label="Address"
              class="tablet:col-span-2"
              @update:model-value="companyStore.updateField('address', $event)"
            />
            <TextInput
              :model-value="companyStore.settings.city"
              label="City"
              @update:model-value="companyStore.updateField('city', $event)"
            />
            <TextInput
              :model-value="companyStore.settings.country"
              label="Country"
              @update:model-value="companyStore.updateField('country', $event)"
            />
          </div>
        </FormSection>

        <FormSection title="Branding" description="Applied to report headers, portals and printable documents.">
          <div class="flex items-center gap-3">
            <input
              type="color"
              :value="companyStore.settings.brandColor"
              class="h-10 w-14 cursor-pointer rounded-md border border-border-default"
              @input="companyStore.updateField('brandColor', ($event.target as HTMLInputElement).value)"
            />
            <TextInput
              :model-value="companyStore.settings.brandColor"
              label="Brand Color"
              class="flex-1"
              @update:model-value="companyStore.updateField('brandColor', $event)"
            />
          </div>

          <div class="flex flex-col gap-2">
            <label class="text-sm font-medium text-text-secondary">Company Logo</label>
            <p class="text-xs text-text-muted">
              Insertable into any Quotation/Contract document template via its Company Logo merge field. Applies
              immediately -- not part of "Save Changes" below.
            </p>
            <div v-if="companyStore.settings.hasLogo" class="flex items-center gap-3">
              <img
                v-if="logoPreviewUrl"
                :src="logoPreviewUrl"
                alt="Company logo"
                class="h-14 w-auto max-w-[10rem] rounded border border-border-light bg-white object-contain p-1"
              />
              <span class="text-sm text-text-secondary">{{ companyStore.settings.logoFilename }}</span>
              <BaseButton variant="ghost" size="sm" :loading="isRemovingLogo" @click="handleLogoRemove">Remove</BaseButton>
            </div>
            <FileUploader
              accept=".png,.jpg,.jpeg"
              :hint="isUploadingLogo ? 'Uploading…' : companyStore.settings.hasLogo ? 'Upload a different logo to replace it' : 'PNG or JPEG'"
              :allowed-extensions="['.png', '.jpg', '.jpeg']"
              :max-size-bytes="5 * 1024 * 1024"
              @select="handleLogoSelect"
            />
          </div>
        </FormSection>

        <FormSection title="Application Preferences" description="Defaults applied across the application.">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <SelectBox
              :model-value="companyStore.settings.defaultLanguage"
              label="Default Language"
              :options="LANGUAGE_OPTIONS"
              @update:model-value="companyStore.updateField('defaultLanguage', $event as AppLanguage)"
            />
            <TextInput
              :model-value="companyStore.settings.timezone"
              label="Timezone"
              @update:model-value="companyStore.updateField('timezone', $event)"
            />
            <SelectBox
              :model-value="companyStore.settings.dateFormat"
              label="Date Format"
              :options="DATE_FORMAT_OPTIONS"
              @update:model-value="companyStore.updateField('dateFormat', $event)"
            />
            <SelectBox
              :model-value="companyStore.settings.currency"
              label="Currency"
              :options="CURRENCY_OPTIONS"
              @update:model-value="companyStore.updateField('currency', $event)"
            />
          </div>
        </FormSection>

        <FormSection title="Business Settings" description="Default terms applied to new quotations.">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <NumberInput
              :model-value="companyStore.settings.defaultPaymentTermsDays"
              label="Default Payment Terms (days)"
              :min="0"
              @update:model-value="companyStore.updateField('defaultPaymentTermsDays', Number($event))"
            />
            <NumberInput
              :model-value="companyStore.settings.defaultQuotationValidityDays"
              label="Default Quotation Validity (days)"
              :min="0"
              @update:model-value="companyStore.updateField('defaultQuotationValidityDays', Number($event))"
            />
          </div>
        </FormSection>

        <FormSection title="Project Alerts" description="Notify the assigned engineer when a project sits without moving forward.">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <NumberInput
              :model-value="companyStore.settings.staleProjectAlertDays"
              label="Stale Project Alert Threshold (days)"
              hint="A notification is sent once a project's workflow stage hasn't advanced for this many days."
              :min="1"
              @update:model-value="companyStore.updateField('staleProjectAlertDays', Number($event))"
            />
          </div>
        </FormSection>

        <FormSection title="Onboarding Alerts" description="Notify the account manager when a client's onboarding sits without moving forward.">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <NumberInput
              :model-value="companyStore.settings.staleOnboardingAlertDays"
              label="Stale Onboarding Alert Threshold (days)"
              hint="A notification is sent once a client's onboarding status hasn't advanced for this many days."
              :min="1"
              @update:model-value="companyStore.updateField('staleOnboardingAlertDays', Number($event))"
            />
          </div>
        </FormSection>

        <FormSection title="Site Engineer Status Reports" description="Whoever is selected here reviews every incoming field status report and attaches it to the relevant project.">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <SelectBox
              :model-value="companyStore.settings.statusReportRecipientId ?? ''"
              label="Status Report Recipient"
              placeholder="No one assigned"
              :options="statusReportRecipientOptions"
              @update:model-value="companyStore.updateField('statusReportRecipientId', $event || null)"
            />
          </div>
        </FormSection>

        <FormActionBar submit-label="Save Changes" :loading="companyStore.isSaving" @submit="handleSave" @cancel="handleCancel" />
      </div>
    </div>
  </div>
</template>
