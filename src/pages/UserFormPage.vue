<script setup lang="ts">
import { ArrowLeft, ArrowRight } from '@lucide/vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'
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
import { useFormValidation } from '@/composables/useFormValidation'
import { useLocale } from '@/composables/useLocale'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { useAuthStore } from '@/stores/authStore'
import { useToastStore } from '@/stores/toastStore'
import { useUserStore } from '@/stores/userStore'
import { uuid } from '@/utils/uuid'
import { validators } from '@/utils/validators'
import type { AppUser, UserRole, UserSalutation } from '@/types/User'
import type { SelectOption } from '@/types/Ui'

// Dedicated route (/admin/users/:userId). The page decides create vs
// edit from whether :userId ('new', or a real id) resolves to an
// existing user, rather than a caller-chosen mode prop.

const ROLE_OPTIONS: SelectOption[] = [
  { label: 'Administrator', value: 'Administrator', labelKey: 'administration.userRole.administrator' },
  { label: 'Project Manager', value: 'Project Manager', labelKey: 'administration.userRole.projectManager' },
  { label: 'Engineer', value: 'Engineer', labelKey: 'administration.userRole.engineer' },
  { label: 'Document Controller', value: 'Document Controller', labelKey: 'administration.userRole.documentController' },
  { label: 'Viewer', value: 'Viewer', labelKey: 'administration.userRole.viewer' },
]

// Not required -- a user with no salutation set just prints as their
// bare name on generated documents. The leading blank option is real
// and selectable (not the SelectBox placeholder, which is disabled
// once something else has been picked) so an admin can explicitly
// clear a salutation back to "none" after setting one.
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
// and only then find out it did nothing.
const isSelf = computed(() => Boolean(existingUser.value) && existingUser.value?.id === authStore.user?.id)

const form = reactive({
  name: '',
  salutation: '' as UserSalutation | '',
  designation: '',
  email: '',
  mobile: '',
  role: '' as UserRole | '',
})
const isActive = ref(true)

const { errors, setRules, validateAll } = useFormValidation()

setRules({
  name: [validators.required(t('administration.userDialog.nameRequired'))],
  email: [validators.required(t('administration.userDialog.emailRequired')), validators.email(t('administration.userDialog.emailInvalid'))],
  role: [validators.required(t('administration.userDialog.roleRequired'))],
})

// `errors` is populated live, not only after a failed submit, so
// Name/Email/Role are flagged red as soon as the page opens (once
// seeded below) if left empty.
function revalidate(): void {
  validateAll(form)
}
watch(form, revalidate, { deep: true })

// Seeds once loading finishes (from the existing user when editing,
// blank otherwise) -- guarded so a later reactive update to
// existingUser doesn't silently discard in-progress edits.
const isFormSeeded = ref(false)
watch(
  () => [isLoading.value, existingUser.value] as const,
  ([loading, user]) => {
    if (loading || isFormSeeded.value) return
    form.name = user?.name ?? ''
    form.salutation = user?.salutation ?? ''
    form.designation = user?.designation ?? ''
    form.email = user?.email ?? ''
    form.mobile = user?.mobile ?? ''
    form.role = user?.role ?? ''
    isActive.value = user ? user.status === 'Active' : true
    isFormSeeded.value = true
    revalidate()
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
  if (!validateAll(form)) return

  const trimmedEmail = form.email.trim()
  const user: AppUser = {
    id: existingUser.value?.id ?? `USR-${uuid().slice(0, 6).toUpperCase()}`,
    name: form.name.trim(),
    salutation: form.salutation || undefined,
    designation: form.designation.trim(),
    email: trimmedEmail,
    mobile: form.mobile.trim(),
    role: form.role as UserRole,
    avatar: initialsFor(form.name.trim()),
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

    <div v-if="isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="7" />
    </div>

    <EmptyState
      v-else-if="!isCreateMode && !existingUser"
      :title="t('administration.userManagementPage.userNotFoundTitle')"
      :description="t('administration.userManagementPage.userNotFoundDescription')"
    />

    <div v-else class="rounded-xl border border-border-light bg-bg-card p-5">
      <h1 class="mb-4 text-lg font-semibold text-text-primary">
        {{ existingUser ? t('administration.userDialog.editTitle') : t('administration.userDialog.addTitle') }}
      </h1>

      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput
            v-model="form.name"
            :label="t('administration.userDialog.fullName')"
            :placeholder="t('administration.userDialog.fullNamePlaceholder')"
            required
            :error="errors.name"
          />
          <SelectBox
            :model-value="form.salutation"
            :label="t('administration.userDialog.salutation')"
            :placeholder="t('administration.userDialog.salutationPlaceholder')"
            :options="SALUTATION_OPTIONS"
            @update:model-value="form.salutation = ($event || '') as UserSalutation | ''"
          />
        </div>

        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput
            v-model="form.designation"
            :label="t('administration.userDialog.designation')"
            :placeholder="t('administration.userDialog.designationPlaceholder')"
          />
          <TextInput
            v-model="form.email"
            type="email"
            :label="t('administration.userDialog.email')"
            :placeholder="t('administration.userDialog.emailPlaceholder')"
            required
            :error="errors.email"
          />
        </div>

        <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
          <TextInput
            v-model="form.mobile"
            type="tel"
            :label="t('administration.userDialog.mobile')"
            :placeholder="t('administration.userDialog.mobilePlaceholder')"
          />
          <div>
            <SelectBox
              :model-value="form.role"
              :label="t('administration.userDialog.role')"
              :placeholder="t('administration.userDialog.rolePlaceholder')"
              :options="ROLE_OPTIONS"
              required
              :disabled="isSelf"
              :error="errors.role"
              @update:model-value="form.role = $event as UserRole"
            />
            <p v-if="isSelf" class="mt-1.5 text-xs text-text-muted">{{ t('administration.userDialog.cannotChangeOwnRole') }}</p>
          </div>
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
