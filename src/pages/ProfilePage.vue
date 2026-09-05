<script setup lang="ts">
import { Mail, Shield } from '@lucide/vue'
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import Avatar from '@/components/common/Avatar.vue'
import Card from '@/components/common/Card.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import FormSection from '@/components/common/FormSection.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import TextInput from '@/components/common/TextInput.vue'
import { useAuth } from '@/composables/useAuthComposable'
import { useToastStore } from '@/stores/toastStore'
import type { UserRole, UserStatus } from '@/types/User'
import { getUserRoleVariant, getUserStatusVariant } from '@/utils/userHelpers'

const { t } = useI18n()
const { user, updateProfile } = useAuth()
const toastStore = useToastStore()

const ROLE_LABEL_KEYS: Record<string, string> = {
  Administrator: 'administration.userRole.administrator',
  'Project Manager': 'administration.userRole.projectManager',
  Engineer: 'administration.userRole.engineer',
  'Document Controller': 'administration.userRole.documentController',
  Viewer: 'administration.userRole.viewer',
}

const STATUS_LABEL_KEYS: Record<string, string> = {
  Active: 'administration.userStatus.active',
  Inactive: 'administration.userStatus.inactive',
}

const userRoleLabel = computed(() => {
  const key = user.value ? ROLE_LABEL_KEYS[user.value.role] : undefined
  return key ? t(key) : (user.value?.role ?? '')
})

const userStatusLabel = computed(() => {
  const key = user.value ? STATUS_LABEL_KEYS[user.value.status] : undefined
  return key ? t(key) : (user.value?.status ?? '')
})

interface ProfileForm {
  name: string
  designation: string
  mobile: string
}

const form = reactive<ProfileForm>({ name: '', designation: '', mobile: '' })
const formError = ref<string>()
const isSaving = ref(false)

function resetForm(): void {
  form.name = user.value?.name ?? ''
  form.designation = user.value?.designation ?? ''
  form.mobile = user.value?.mobile ?? ''
  formError.value = undefined
}

// Seed the form as soon as the user is available, and re-seed if the
// store's copy changes underneath us (e.g. a save from elsewhere) --
// but not while the person still has unsaved edits of their own.
watch(
  user,
  () => {
    if (!isDirty.value) resetForm()
  },
  { immediate: true },
)

const isDirty = computed(
  () =>
    form.name !== (user.value?.name ?? '') ||
    form.designation !== (user.value?.designation ?? '') ||
    form.mobile !== (user.value?.mobile ?? ''),
)

const canSubmit = computed(() => isDirty.value && form.name.trim().length > 0)

async function handleSave(): Promise<void> {
  if (!canSubmit.value) return
  formError.value = undefined
  isSaving.value = true
  try {
    await updateProfile({
      name: form.name.trim(),
      designation: form.designation.trim() || null,
      mobile: form.mobile.trim() || null,
    })
    toastStore.show('success', 'Profile updated', 'Your changes have been saved.')
  } catch (error) {
    formError.value = error instanceof Error && error.message ? error.message : 'Failed to update profile.'
  } finally {
    isSaving.value = false
  }
}

function handleCancel(): void {
  resetForm()
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6 laptop:p-8">
    <PageHeader :title="t('profile.pageTitle')" :subtitle="t('profile.pageSubtitle')" />

    <div v-if="user" class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <Card>
        <div class="flex flex-col items-center gap-3 text-center">
          <Avatar :name="user.name" size="lg" />
          <div>
            <p class="text-base font-semibold text-text-primary">{{ user.name }}</p>
            <p class="text-sm text-text-muted">{{ user.designation || user.role }}</p>
          </div>
          <div class="flex flex-wrap items-center justify-center gap-2">
            <StatusBadge :label="userRoleLabel" :variant="getUserRoleVariant(user.role as UserRole)" />
            <StatusBadge :label="userStatusLabel" :variant="getUserStatusVariant(user.status as UserStatus)" />
          </div>
        </div>

        <div class="mt-5 flex flex-col gap-2 border-t border-border-light pt-4 text-sm text-text-secondary">
          <div class="flex items-center gap-2">
            <Mail class="h-4 w-4 shrink-0 text-text-muted" />
            <span class="truncate">{{ user.email }}</span>
          </div>
          <div class="flex items-center gap-2">
            <Shield class="h-4 w-4 shrink-0 text-text-muted" />
            <span>{{ user.id }}</span>
          </div>
        </div>
      </Card>

      <div class="flex flex-col gap-8 rounded-xl border border-border-light bg-bg-card p-6 laptop:col-span-2">
        <FormSection :title="t('profile.personalDetails')" :description="t('profile.personalDetailsDescription')">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <TextInput v-model="form.name" :label="t('profile.fullName')" required :error="formError" class="tablet:col-span-2" />
            <TextInput v-model="form.designation" :label="t('profile.designation')" :placeholder="t('profile.designationPlaceholder')" />
            <TextInput v-model="form.mobile" type="tel" :label="t('profile.mobile')" :placeholder="t('profile.mobilePlaceholder')" />
          </div>
        </FormSection>

        <FormSection :title="t('profile.account')" :description="t('profile.accountDescription')">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <TextInput :model-value="user.email" type="email" :label="t('profile.email')" disabled />
            <TextInput :model-value="userRoleLabel" :label="t('profile.role')" disabled />
          </div>
        </FormSection>

        <FormActionBar :submit-label="t('profile.saveChanges')" :loading="isSaving" :disabled="!canSubmit" @submit="handleSave" @cancel="handleCancel" />
      </div>
    </div>
  </div>
</template>
