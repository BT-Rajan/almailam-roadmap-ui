<script setup lang="ts">
import { reactive, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextInput from '@/components/common/TextInput.vue'
import { CLIENT_ADDRESS_TYPE_OPTIONS } from '@/constants/clientOptions'
import type { ClientAddress, ClientAddressType } from '@/types/Client'

const props = defineProps<{
  modelValue: boolean
  address?: ClientAddress
  loading?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [
    payload: {
      addressType: ClientAddressType
      country: string
      state: string
      city: string
      area: string
      street: string
      building: string
    },
  ]
}>()

function emptyForm() {
  return { addressType: 'Registered' as ClientAddressType, country: '', state: '', city: '', area: '', street: '', building: '' }
}

const form = reactive(emptyForm())
const errors = reactive({ country: '', state: '', city: '' })

watch(
  () => props.modelValue,
  (open) => {
    if (!open) return
    Object.assign(
      form,
      props.address
        ? { ...props.address, area: props.address.area ?? '', street: props.address.street ?? '', building: props.address.building ?? '' }
        : emptyForm(),
    )
    errors.country = ''
    errors.state = ''
    errors.city = ''
  },
)

function closeDialog(): void {
  emit('update:modelValue', false)
}

function handleConfirm(): void {
  errors.country = form.country.trim() ? '' : 'Country is required'
  errors.state = form.state.trim() ? '' : 'Governorate / State is required'
  errors.city = form.city.trim() ? '' : 'City is required'
  if (errors.country || errors.state || errors.city) return

  emit('confirm', { ...form })
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="address ? 'Edit Address' : 'Add Address'"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="flex flex-col gap-4">
      <SelectBox v-model="form.addressType" label="Address Type" :options="CLIENT_ADDRESS_TYPE_OPTIONS" />
      <TextInput v-model="form.country" label="Country" required :error="errors.country" />
      <TextInput v-model="form.state" label="Governorate / State" required :error="errors.state" />
      <TextInput v-model="form.city" label="City" required :error="errors.city" />
      <TextInput v-model="form.area" label="Area" />
      <TextInput v-model="form.street" label="Street" />
      <TextInput v-model="form.building" label="Building" />
    </div>

    <template #footer>
      <BaseButton variant="secondary" @click="closeDialog">Cancel</BaseButton>
      <BaseButton :loading="loading" @click="handleConfirm">{{ address ? 'Save Changes' : 'Add Address' }}</BaseButton>
    </template>
  </BaseDialog>
</template>
