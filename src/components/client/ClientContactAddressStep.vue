<script setup lang="ts">
import { Plus, Trash2 } from '@lucide/vue'

import BaseButton from '@/components/common/BaseButton.vue'
import FormSection from '@/components/common/FormSection.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import ToggleSwitch from '@/components/common/ToggleSwitch.vue'
import { CLIENT_ADDRESS_TYPE_OPTIONS, CLIENT_CONTACT_TYPE_OPTIONS } from '@/constants/clientOptions'
import type { ClientWizardForm } from '@/types/ClientWizard'
import type { FieldErrors } from '@/utils/clientValidation'

defineProps<{
  contactErrors: FieldErrors[]
  contactsFormError?: string
  addressErrors: FieldErrors
}>()

const form = defineModel<ClientWizardForm>({ required: true })

function addContact(): void {
  form.value.contacts.push({
    name: '',
    contactType: 'Other',
    mobile: '',
    email: '',
    isAuthorisedRepresentative: false,
  })
}

function removeContact(index: number): void {
  form.value.contacts.splice(index, 1)
}

// Same one-directional sync as ClientContactEditDialog.vue: explicitly
// typing someone as the authorised representative always implies the
// flag; the reverse isn't forced.
function handleContactTypeChange(index: number, type: string): void {
  if (type === 'Authorised Representative') {
    form.value.contacts[index].isAuthorisedRepresentative = true
  }
}
</script>

<template>
  <div class="flex flex-col gap-6">
    <FormSection title="Contacts" description="Optional -- add a contact for this client if one is available.">
      <div class="flex flex-col gap-4">
        <p v-if="contactsFormError" class="text-xs text-danger-500">{{ contactsFormError }}</p>
        <div
          v-for="(contact, index) in form.contacts"
          :key="index"
          class="flex flex-col gap-3 rounded-lg border border-border-light p-4"
        >
          <div class="flex items-center justify-between">
            <p class="text-sm font-medium text-text-secondary">Contact {{ index + 1 }}</p>
            <button
              v-if="form.contacts.length > 1"
              type="button"
              aria-label="Remove contact"
              class="text-text-muted hover:text-danger-500"
              @click="removeContact(index)"
            >
              <Trash2 class="h-4 w-4" />
            </button>
          </div>
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <TextInput v-model="contact.name" label="Name" :error="contactErrors[index]?.name" />
            <SelectBox
              v-model="contact.contactType"
              label="Contact Type"
              :options="CLIENT_CONTACT_TYPE_OPTIONS"
              @update:model-value="(value) => handleContactTypeChange(index, value)"
            />
            <TextInput v-model="contact.mobile" label="Mobile Number" :error="contactErrors[index]?.mobile" />
            <TextInput v-model="contact.email" label="Email Address" type="email" :error="contactErrors[index]?.email" />
          </div>
          <ToggleSwitch v-model="contact.isAuthorisedRepresentative" label="Authorised to Act on Client's Behalf" />
        </div>
        <BaseButton variant="secondary" :icon="Plus" size="sm" @click="addContact">Add Contact</BaseButton>
      </div>
    </FormSection>

    <FormSection title="Address" description="Optional -- add an address if one is available.">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <SelectBox v-model="form.address.addressType" label="Address Type" :options="CLIENT_ADDRESS_TYPE_OPTIONS" />
        <TextInput v-model="form.address.country" label="Country" :error="addressErrors.country" />
        <TextInput v-model="form.address.state" label="Governorate / State" :error="addressErrors.state" />
        <TextInput v-model="form.address.city" label="City" :error="addressErrors.city" />
        <TextInput v-model="form.address.area" label="Area" />
        <TextInput v-model="form.address.street" label="Street" />
        <TextInput v-model="form.address.building" label="Building" />
      </div>
    </FormSection>
  </div>
</template>
