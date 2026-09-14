<script setup lang="ts">
import { ArrowLeft, ArrowRight } from '@lucide/vue'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import TextInput from '@/components/common/TextInput.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import PasswordResetDialog from '@/components/administration/PasswordResetDialog.vue'
import { useLocale } from '@/composables/useLocale'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import { uuid } from '@/utils/uuid'
import { validators } from '@/utils/validators'
import type { AppUser, UserRole, UserSalutation } from '@/types/User'
import type { SelectOption } from '@/types/Ui'

// Replaces UserDialog.vue's modal -- a dedicated route
// (/admin/users/:userId), same treatment as
// ScheduledReportFormPage.vue/PaymentPlanFormPage.vue: the page decides
// create vs edit itself from whether :userId ('new', or a real id)
// resolves to an existing user, rather than a caller-chosen mode prop.

const ROLE_OPTIONS: SelectOption[] = [
  { label: 'Administrator', value: 'Administrator', labelKey: 'administration.userRole.administrator' },
  { label: 'Project Manager', value: 'Project Manager', labelKey: 'administration.userRole.projectManager' },
  { label: 'Engineer', value: 'Engineer', labelKey: 'administration.userRole.engineer' },
  { label: 'Document Controller', value: 'Document Controller', labelKey: 'administration.userRole.documentController' },
  { label: 'Viewer', value: 'Viewer', labelKey: 'administration.userRole.viewer' },
]

// Not required -- a user with no salutation set just keeps printing as
// their bare name on generated documents (see backend migration 0097),
// same as every user did before this field existed. The leading blank
// option is real and selectable (not the SelectBox placeholder, which
// is disabled once something else has been picked) so an admin can
// explicitly clear a salutation back to "none" after setting one.
const SALUTATION_OPTIONS: SelectOption[] = [
  { label: 'Not specified', value: '', labelKey: 'administration.userDialog.salutationNone' },
  { label: 'Mr.', value: 'Mr.', labelKey: 'administration.userDialog.salutationMr' },
  { label: 'Ms.', value: 'Ms.', labelKey: 'administration.userDialog.salutationMs' },
]

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const { isRtl } = useLocale()
const authStore = useAuthStore()
const userStore = useUserStore()
const toastStore = useToastStore()

const backIcon = computed(() => (isRtl.value ? ArrowRight : ArrowLeft))
const userId = computed(() => route.params.userId as string)
const isCreateMode = computed(() => userId.value === 'new')

const isLoading = ref(true)
async function loadData(): Promise<void> {
  isLoading.value = true
  if (userStore.users.length === 0) await userStore.loadUsers()
  isLoading.value = false
}
onMounted(loadData)

const existingUser = computed(() =>
  isCreateMode.value ? undefined : userStore.users.find((user) => user.id === userId.value),
)

function goBack(): void {
  router.push({ name: ROUTE_NAMES.ADMIN_USERS })
}

// The backend rejects changing your own role outright
// (user_service.update_user: "You cannot change your own role.") --
// disabling it here instead of letting someone pick a new role, submit,
// and only then find out it did nothing, matching the same
// self-protection treatment UserManagementPage.vue's own Delete/
// Deactivate buttons already give (both hide themselves when the
// profile being viewed is your own).
const isSelf = computed(() => Boolean(existingUser.value) && existingUser.value?.id === authStore.user?.id)

const name = ref('')
const salutation = ref<UserSalutation | ''>('')
const designation = ref('')
const email = ref('')
const mobile = ref('')
const role = ref<UserRole | ''>('')
const isActive = ref(true)
const nameError = ref<string>()
const emailError = ref<string>()
const roleError = ref<string>()

// Seeds once loading finishes (from the existing user when editing,
// blank otherwise) -- guarded so a later reactive update to
// existingUser doesn't silently discard in-progress edits.
const isFormSeeded = ref(false)
watch(
  () => [isLoading.value, existingUser.value] as const,
  ([loading, user]) => {
    if (loading || isFormSeeded.value) return
    name.value = user?.name ?? ''
    salutation.value = user?.salutation ?? ''
    designation.value = user?.designation ?? ''
    email.value = user?.email ?? ''
    mobile.value = user?.mobile ?? ''
    role.value = user?.role ?? ''
    isActive.value = user ? user.status === 'Active' : true
    isFormSeeded.value = true
  },
  { immediate: true },
)

function initialsFor(fullName: string): string {
  const parts = fullName.trim().split(/\s+/)
  return ((parts[0]?.charAt(0) ?? '') + (parts.length > 1 ? (parts[parts.length - 1]?.charAt(0) ?? '') : '')).toUpperCase()
}

const isSaving = ref(false)
const isPasswordResultOpen = ref(false)
const createdPassword = ref('')
const createdUserName = ref('')

async function submitForm(): Promise<void> {
  nameError.value = name.value.trim().length === 0 ? t('administration.userDialog.nameRequired') : undefined

  const trimmedEmail = email.value.trim()
  if (trimmedEmail.length === 0) {
    emailError.value = t('administration.userDialog.emailRequired')
  } else {
    // Reuses the same shared email-format check as everywhere else in
    // the app (validators.ts) instead of a separate, slightly different
    // regex.
    const check = validators.email(t('administration.userDialog.emailInvalid'))(trimmedEmail)
    emailError.value = check === true ? undefined : check
  }

  roleError.value = role.value === '' ? t('administration.userDialog.roleRequired') : undefined

  if (nameError.value || emailError.value || roleError.value) return

  const user: AppUser = {
    id: existingUser.value?.id ?? `USR-${uuid().slice(0, 6).toUpperCase()}`,
    name: name.value.trim(),
    salutation: salutation.value || undefined,
    designation: designation.value.trim(),
    email: trimmedEmail,
    mobile: mobile.value.trim(),
    role: role.value as UserRole,
    avatar: initialsFor(name.value.trim()),
    status: isActive.value ? 'Active' : 'Inactive',
  }

  isSaving.value = true
  try {
    if (existingUser.value) {
      await userStore.saveUser(user)
      toastStore.show('success', t('administration.userManagementPage.userUpdatedTitle'), t('administration.userManagementPage.userUpdatedDescription', { name: user.name }))
      goBack()
    } else {
      const created = await userStore.addUser(user)
      toastStore.show('success', t('administration.userManagementPage.userAddedTitle'), t('administration.userManagementPage.userAddedDescription', { name: created.name }))
      createdUserName.value = created.name
      createdPassword.value = created.temporaryPassword
      isPasswordResultOpen.value = true
    }
  } catch (error) {
    toastStore.show(
      'error',
      existingUser.value ? t('administration.userManagementPage.failedToUpdateUser') : t('administration.userManagementPage.failedToAddUser'),
      error instanceof Error ? error.message : t('common.pleaseTryAgain'),
    )
  } finally {
    isSaving.value = false
  }
}

// Only closable via its own "Done" button (see PasswordResetDialog.vue:
// closable="false") -- this only fires once the admin has actually
// dismissed it, not on the save itself, so they don't lose the one
// chance to see/copy the temporary password.
function handlePasswordDialogClosed(open: boolean): void {
  isPasswordResultOpen.value = open
  if (!open) goBack()
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <BaseButton variant="ghost" size="sm" :icon="backIcon" class="self-start no-print" @click="goBack">
      {{ t('administration.userManagementPage.backToUsers') }}
    </BaseButton>

    <div v-if="isLoading" class="max-w-2xl rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="7" />
    </div>

    <EmptyState
      v-else-if="!isCreateMode && !existingUser"
      :title="t('administration.userManagementPage.userNotFoundTitle')"
      :description="t('administration.userManagementPage.userNotFoundDescription')"
    />

    <div v-else class="max-w-2xl rounded-xl border border-border-light bg-bg-card p-5">
      <h1 class="mb-4 text-lg font-semibold text-text-primary">
        {{ existingUser ? t('administration.userDialog.editTitle') : t('administration.userDialog.addTitle') }}
      </h1>

      <div class="flex flex-col gap-4">
        <TextInput
          v-model="name"
          :label="t('administration.userDialog.fullName')"
          :placeholder="t('administration.userDialog.fullNamePlaceholder')"
          required
          :error="nameError"
        />
        <SelectBox
          :model-value="salutation"
          :label="t('administration.userDialog.salutation')"
          :placeholder="t('administration.userDialog.salutationPlaceholder')"
          :options="SALUTATION_OPTIONS"
          @update:model-value="salutation = ($event || '') as UserSalutation | ''"
        />
        <TextInput
          v-model="designation"
          :label="t('administration.userDialog.designation')"
          :placeholder="t('administration.userDialog.designationPlaceholder')"
        />
        <TextInput
          v-model="email"
          type="email"
          :label="t('administration.userDialog.email')"
          :placeholder="t('administration.userDialog.emailPlaceholder')"
          required
          :error="emailError"
        />
        <TextInput
          v-model="mobile"
          type="tel"
          :label="t('administration.userDialog.mobile')"
          :placeholder="t('administration.userDialog.mobilePlaceholder')"
        />
        <div>
          <SelectBox
            :model-value="role"
            :label="t('administration.userDialog.role')"
            :placeholder="t('administration.userDialog.rolePlaceholder')"
            :options="ROLE_OPTIONS"
            required
            :disabled="isSelf"
            :error="roleError"
            @update:model-value="role = $event as UserRole"
          />
          <p v-if="isSelf" class="mt-1.5 text-xs text-text-muted">{{ t('administration.userDialog.cannotChangeOwnRole') }}</p>
        </div>
        <ToggleSwitch
          v-model="isActive"
          :label="t('administration.userDialog.active')"
          :disabled="isSelf"
          :hint="isSelf ? t('administration.userDialog.cannotDeactivateOwnAccount') : t('administration.userDialog.activeHint')"
        />
      </div>

      <FormActionBar
        class="mt-6"
        :submit-label="existingUser ? t('administration.userDialog.saveChanges') : t('administration.userDialog.addUser')"
        :loading="isSaving"
        @submit="submitForm"
        @cancel="goBack"
      />
    </div>

    <PasswordResetDialog
      :model-value="isPasswordResultOpen"
      :user-name="createdUserName"
      :password="createdPassword"
      :heading="t('administration.userManagementPage.loginCreatedFor', { name: createdUserName })"
      @update:model-value="handlePasswordDialogClosed"
    />
  </div>
</template>
