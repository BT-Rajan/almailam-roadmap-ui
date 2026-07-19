<script setup lang="ts">
import { ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import TextArea from '@/components/common/TextArea.vue'
import TextInput from '@/components/common/TextInput.vue'
import type { PromptTemplate } from '@/types/AiConfig'

interface Props {
  modelValue: boolean
  template?: PromptTemplate
  saving?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  template: undefined,
  saving: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [input: Omit<PromptTemplate, 'id'>]
}>()

const form = ref({ name: '', description: '', template: '' })
const errors = ref<Record<string, string>>({})

watch(
  () => [props.modelValue, props.template] as const,
  ([isOpen, template]) => {
    if (!isOpen || !template) return
    form.value = { name: template.name, description: template.description, template: template.template }
    errors.value = {}
  },
  { immediate: true },
)

function validate(): boolean {
  errors.value = {}
  if (!form.value.name.trim()) errors.value.name = 'Template name is required'
  if (!form.value.template.trim()) errors.value.template = 'Prompt text is required'
  return Object.keys(errors.value).length === 0
}

function handleSave(): void {
  if (!validate() || !props.template) return
  emit('save', { name: form.value.name.trim(), description: form.value.description.trim(), template: form.value.template.trim(), module: props.template.module })
}
</script>

<template>
  <BaseDialog :model-value="modelValue" title="Edit Prompt Template" size="lg" @update:model-value="emit('update:modelValue', $event)">
    <div class="flex flex-col gap-4">
      <TextInput v-model="form.name" label="Template Name" :error="errors.name" required />
      <TextInput v-model="form.description" label="Description" />
      <TextArea v-model="form.template" label="Prompt Text" hint="This is the instruction sent to the AI provider." :rows="6" :error="errors.template" required />
    </div>

    <template #footer>
      <BaseButton variant="secondary" :disabled="saving" @click="emit('update:modelValue', false)">Cancel</BaseButton>
      <BaseButton :loading="saving" @click="handleSave">Save Template</BaseButton>
    </template>
  </BaseDialog>
</template>
