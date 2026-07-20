<script setup lang="ts">
import { Plus, Trash2 } from '@lucide/vue'

import BaseButton from '@/components/common/BaseButton.vue'
import FormSection from '@/components/common/FormSection.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { CLIENT_ADDRESS_TYPE_OPTIONS, CLIENT_CONTACT_TYPE_OPTIONS } from '@/constants/clientOptions'
import type { ClientWizardForm } from '@/types/ClientWizard'

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
</script>

<template>
  <div class="flex flex-col gap-6">
    <FormSection title="Contacts" description="Add at least one contact for this client.">
      <div class="flex flex-col gap-4">
        <div
          v-for="(contact, index) in form.contacts"
          :key="index"
          class="flex flex-col gap-3 rounded-lg border border-border-light p-4"
        >
          <div class="flex items-center justify-between">
            <p class="text-sm font-medium text-neutral-700">Contact {{ index + 1 }}</p>
            <button
              v-if="form.contacts.length > 1"
              type="button"
              aria-label="Remove contact"
              class="text-neutral-400 hover:text-danger-500"
              @click="removeContact(index)"
            >
              <Trash2 class="h-4 w-4" />
            </button>
          </div>
          <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
            <TextInput v-model="contact.name" label="Name" required />
            <SelectBox v-model="contact.contactType" label="Contact Type" :options="CLIENT_CONTACT_TYPE_OPTIONS" />
            <TextInput v-model="contact.mobile" label="Mobile Number" required />
            <TextInput v-model="contact.email" label="Email Address" type="email" required />
          </div>
        </div>
        <BaseButton variant="secondary" :icon="Plus" size="sm" @click="addContact">Add Contact</BaseButton>
      </div>
    </FormSection>

    <FormSection title="Address">
      <div class="grid grid-cols-1 gap-4 tablet:grid-cols-2">
        <SelectBox v-model="form.address.addressType" label="Address Type" :options="CLIENT_ADDRESS_TYPE_OPTIONS" />
        <TextInput v-model="form.address.country" label="Country" required />
        <TextInput v-model="form.address.state" label="Governorate / State" />
        <TextInput v-model="form.address.city" label="City" required />
        <TextInput v-model="form.address.area" label="Area" />
        <TextInput v-model="form.address.street" label="Street" />
        <TextInput v-model="form.address.building" label="Building" />
      </div>
    </FormSection>
  </div>
</template>
