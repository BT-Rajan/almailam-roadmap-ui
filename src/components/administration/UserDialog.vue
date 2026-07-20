<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import BaseDialog from '@/components/common/BaseDialog.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import type { AppUser, UserRole } from '@/types/User'
import type { SelectOption } from '@/types/Ui'

const ROLE_OPTIONS: SelectOption[] = [
  { label: 'Administrator', value: 'Administrator' },
  { label: 'Project Manager', value: 'Project Manager' },
  { label: 'Engineer', value: 'Engineer' },
  { label: 'Document Controller', value: 'Document Controller' },
  { label: 'Viewer', value: 'Viewer' },
]

const props = defineProps<{
  modelValue: boolean
  user?: AppUser
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [user: AppUser]
}>()

const name = ref('')
const designation = ref('')
const email = ref('')
const mobile = ref('')
const role = ref<UserRole | ''>('')
const isActive = ref(true)
const nameError = ref<string>()
const emailError = ref<string>()

const isEditMode = computed(() => Boolean(props.user))
const dialogTitle = computed(() => (isEditMode.value ? 'Edit User' : 'Add User'))

function resetForm(): void {
  const source = props.user
  name.value = source?.name ?? ''
  designation.value = source?.designation ?? ''
  email.value = source?.email ?? ''
  mobile.value = source?.mobile ?? ''
  role.value = source?.role ?? ''
  isActive.value = source ? source.status === 'Active' : true
  nameError.value = undefined
  emailError.value = undefined
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) resetForm()
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function initialsFor(fullName: string): string {
  const parts = fullName.trim().split(/\s+/)
  return ((parts[0]?.charAt(0) ?? '') + (parts.length > 1 ? (parts[parts.length - 1]?.charAt(0) ?? '') : '')).toUpperCase()
}

function submitForm(): void {
  nameError.value = name.value.trim().length === 0 ? 'Name is required' : undefined
  emailError.value = /^\S+@\S+\.\S+$/.test(email.value.trim()) ? undefined : 'Enter a valid email address'

  if (nameError.value || emailError.value || role.value === '') return

  const user: AppUser = {
    id: props.user?.id ?? `USR-${crypto.randomUUID().slice(0, 6).toUpperCase()}`,
    name: name.value.trim(),
    designation: designation.value.trim(),
    email: email.value.trim(),
    mobile: mobile.value.trim(),
    role: role.value,
    avatar: initialsFor(name.value.trim()),
    status: isActive.value ? 'Active' : 'Inactive',
  }

  emit('save', user)
  closeDialog()
}
</script>

<template>
  <BaseDialog :model-value="modelValue" :title="dialogTitle" size="md" @update:model-value="closeDialog">
    <div class="flex flex-col gap-4">
      <TextInput v-model="name" label="Full Name" placeholder="e.g. Sara Abdullah" required :error="nameError" />
      <TextInput v-model="designation" label="Designation" placeholder="e.g. Document Controller" />
      <TextInput v-model="email" type="email" label="Email" placeholder="name@almailam.ae" required :error="emailError" />
      <TextInput v-model="mobile" type="tel" label="Mobile" placeholder="+971 50 000 0000" />
      <SelectBox
        :model-value="role"
        label="Role"
        placeholder="Select role"
        :options="ROLE_OPTIONS"
        required
        @update:model-value="role = $event as UserRole"
      />
      <ToggleSwitch v-model="isActive" label="Active" hint="Inactive users cannot sign in." />
    </div>

    <template #footer>
      <FormActionBar :submit-label="isEditMode ? 'Save Changes' : 'Add User'" @submit="submitForm" @cancel="closeDialog" />
    </template>
  </BaseDialog>
</template>
