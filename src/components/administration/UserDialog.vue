<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseDialog from '@/components/common/BaseDialog.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { uuid } from '@/utils/uuid'
import { validators } from '@/utils/validators'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import { useAuthStore } from '@/stores/authStore'
import type { AppUser, UserRole, UserSalutation } from '@/types/User'
import type { SelectOption } from '@/types/Ui'

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

const props = defineProps<{
  modelValue: boolean
  user?: AppUser
  saving?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [user: AppUser]
}>()

const { t } = useI18n()
const authStore = useAuthStore()

// The backend rejects changing your own role outright
// (user_service.update_user: "You cannot change your own role.") --
// disabling it here instead of letting someone pick a new role, submit,
// and only then find out it did nothing, matching the same
// self-protection treatment UserManagementPage.vue's own Delete/
// Deactivate buttons already give (both hide themselves when the
// profile being viewed is your own).
const isSelf = computed(() => Boolean(props.user) && props.user?.id === authStore.user?.id)

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

const isEditMode = computed(() => Boolean(props.user))
const dialogTitle = computed(() =>
  isEditMode.value ? t('administration.userDialog.editTitle') : t('administration.userDialog.addTitle'),
)

function resetForm(): void {
  const source = props.user
  name.value = source?.name ?? ''
  salutation.value = source?.salutation ?? ''
  designation.value = source?.designation ?? ''
  email.value = source?.email ?? ''
  mobile.value = source?.mobile ?? ''
  role.value = source?.role ?? ''
  isActive.value = source ? source.status === 'Active' : true
  nameError.value = undefined
  emailError.value = undefined
  roleError.value = undefined
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) resetForm()
  },
)

function closeDialog(): void {
  if (props.saving) return
  emit('update:modelValue', false)
}

function initialsFor(fullName: string): string {
  const parts = fullName.trim().split(/\s+/)
  return ((parts[0]?.charAt(0) ?? '') + (parts.length > 1 ? (parts[parts.length - 1]?.charAt(0) ?? '') : '')).toUpperCase()
}

function submitForm(): void {
  nameError.value = name.value.trim().length === 0 ? t('administration.userDialog.nameRequired') : undefined

  const trimmedEmail = email.value.trim()
  if (trimmedEmail.length === 0) {
    emailError.value = t('administration.userDialog.emailRequired')
  } else {
    // Reuses the same shared email-format check as everywhere else in
    // the app (validators.ts) instead of this dialog's own separate,
    // slightly different regex.
    const check = validators.email(t('administration.userDialog.emailInvalid'))(trimmedEmail)
    emailError.value = check === true ? undefined : check
  }

  roleError.value = role.value === '' ? t('administration.userDialog.roleRequired') : undefined

  if (nameError.value || emailError.value || roleError.value) return

  const user: AppUser = {
    id: props.user?.id ?? `USR-${uuid().slice(0, 6).toUpperCase()}`,
    name: name.value.trim(),
    salutation: salutation.value || undefined,
    designation: designation.value.trim(),
    email: email.value.trim(),
    mobile: mobile.value.trim(),
    role: role.value as UserRole,
    avatar: initialsFor(name.value.trim()),
    status: isActive.value ? 'Active' : 'Inactive',
  }

  // Not closeDialog() here -- the parent owns whether the save actually
  // succeeded (see UserManagementPage.vue's handleSave) and closes this
  // dialog itself on success. Closing unconditionally on submit is what
  // made a failed save look identical to a successful one: the dialog
  // would close either way and nothing told the admin their data never
  // reached the backend.
  emit('save', user)
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="dialogTitle" size="md" :closable="!saving" @update:model-value="closeDialog">
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

    <template #footer>
      <FormActionBar
        :submit-label="isEditMode ? t('administration.userDialog.saveChanges') : t('administration.userDialog.addUser')"
        :loading="saving"
        @submit="submitForm"
        @cancel="closeDialog"
      />
    </template>
  </BaseDialog>
</template>
