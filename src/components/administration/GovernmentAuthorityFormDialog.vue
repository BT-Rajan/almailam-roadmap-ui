<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import SelectBox from '@/components/common/SelectBox.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import { AUTHORITY_CATEGORY_OPTIONS } from '@/constants/governmentFormOptions'
import type { AuthorityInput } from '@/services/governmentFormService'
import type { AuthorityCategory, GovernmentAuthority } from '@/types/Government'

interface Props {
  modelValue: boolean
  authority?: GovernmentAuthority
  saving?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  authority: undefined,
  saving: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [input: AuthorityInput]
}>()

const { t } = useI18n()

function emptyForm(): AuthorityInput {
  return { name: '', category: 'Municipality', website: '', description: '' }
}

const form = ref<AuthorityInput>(emptyForm())
const errors = ref<Record<string, string>>({})

watch(
  () => [props.modelValue, props.authority] as const,
  ([isOpen, authority]) => {
    if (!isOpen) return
    form.value = authority
      ? { name: authority.name, category: authority.category, website: authority.website, description: authority.description }
      : emptyForm()
    errors.value = {}
  },
  { immediate: true },
)

function validate(): boolean {
  errors.value = {}
  if (!form.value.name.trim()) errors.value.name = 'Authority name is required'
  if (!form.value.website.trim()) errors.value.website = 'Website is required'
  if (!form.value.description.trim()) errors.value.description = 'Description is required'
  return Object.keys(errors.value).length === 0
}

function handleSave(): void {
  if (!validate()) return
  emit('save', { ...form.value, category: form.value.category as AuthorityCategory })
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="authority ? t('administration.authorityFormDialog.editTitle') : t('administration.authorityFormDialog.addTitle')"
    size="md"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="flex flex-col gap-4">
      <TextInput
        v-model="form.name"
        :label="t('administration.authorityFormDialog.authorityName')"
        :placeholder="t('administration.authorityFormDialog.authorityNamePlaceholder')"
        :error="errors.name"
        required
      />
      <SelectBox v-model="form.category" :label="t('administration.authorityFormDialog.category')" :options="AUTHORITY_CATEGORY_OPTIONS" required />
      <TextInput
        v-model="form.website"
        :label="t('administration.authorityFormDialog.website')"
        :placeholder="t('administration.authorityFormDialog.websitePlaceholder')"
        :error="errors.website"
        required
      />
      <TextArea v-model="form.description" :label="t('administration.authorityFormDialog.description')" :rows="3" :error="errors.description" required />
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="saving" @click="emit('update:modelValue', false)">{{ t('common.cancel') }}</BaseButton>
      <BaseButton :loading="saving" @click="handleSave">{{ t('administration.authorityFormDialog.saveAuthority') }}</BaseButton>
    </template>
  </BaseDialog>
</template>
