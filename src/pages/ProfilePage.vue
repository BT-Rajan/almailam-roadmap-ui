<script setup lang="ts">
import { Mail, Shield } from '@lucide/vue'
import { computed, reactive, ref, watch } from 'vue'

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

const { user, updateProfile } = useAuth()
const toastStore = useToastStore()

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
    <PageHeader title="My Profile" subtitle="View and update your personal details." />

    <div v-if="user" class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <Card>
        <div class="flex flex-col items-center gap-3 text-center">
          <Avatar :name="user.name" size="lg" />
          <div>
            <p class="text-base font-semibold text-text-primary">{{ user.name }}</p>
            <p class="text-sm text-text-muted">{{ user.designation || user.role }}</p>
          </div>
          <div class="flex flex-wrap items-center justify-center gap-2">
            <StatusBadge :label="user.role" :variant="getUserRoleVariant(user.role as UserRole)" />
            <StatusBadge :label="user.status" :variant="getUserStatusVariant(user.status as UserStatus)" />
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
        <FormSection title="Personal Details" description="These details appear across the app and on documents you're assigned to.">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <TextInput v-model="form.name" label="Full Name" required :error="formError" class="tablet:col-span-2" />
            <TextInput v-model="form.designation" label="Designation" placeholder="e.g. Senior Engineer" />
            <TextInput v-model="form.mobile" type="tel" label="Mobile" placeholder="e.g. +971 50 000 0000" />
          </div>
        </FormSection>

        <FormSection title="Account" description="Managed by an administrator -- contact one to change these.">
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <TextInput :model-value="user.email" type="email" label="Email" disabled />
            <TextInput :model-value="user.role" label="Role" disabled />
          </div>
        </FormSection>

        <FormActionBar submit-label="Save Changes" :loading="isSaving" :disabled="!canSubmit" @submit="handleSave" @cancel="handleCancel" />
      </div>
    </div>
  </div>
</template>
