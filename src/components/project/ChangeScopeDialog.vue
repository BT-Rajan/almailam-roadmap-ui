<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import RadioGroup from '@/components/common/RadioGroup.vue'
import TextArea from '@/components/common/TextArea.vue'
import type { SelectOption } from '@/types/Ui'

interface Props {
  modelValue: boolean
  currentDescription: string
  isSubmitting?: boolean
}

const props = withDefaults(defineProps<Props>(), { isSubmitting: false })

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [description: string, contractUpdateNeeded: boolean, paymentUpdateNeeded: boolean]
}>()

// Two steps: edit the scope text, then -- only if it actually changed
// -- confirm whether Contract/Payment need to catch up with it. A
// no-op edit (reopened and closed without changing anything) skips
// the second step entirely rather than asking two pointless questions.
const step = ref<'edit' | 'confirm'>('edit')
const descriptionDraft = ref('')
const contractUpdateNeeded = ref<'yes' | 'no'>('no')
const paymentUpdateNeeded = ref<'yes' | 'no'>('no')

const YES_NO_OPTIONS: SelectOption[] = [
  { label: 'Yes', value: 'yes' },
  { label: 'No', value: 'no' },
]

watch(
  () => props.modelValue,
  (isOpen) => {
    if (!isOpen) return
    step.value = 'edit'
    descriptionDraft.value = props.currentDescription
    contractUpdateNeeded.value = 'no'
    paymentUpdateNeeded.value = 'no'
  },
)

const hasChanged = computed(() => descriptionDraft.value.trim() !== props.currentDescription.trim())
const canContinue = computed(() => descriptionDraft.value.trim().length > 0)

function handleCancel(): void {
  emit('update:modelValue', false)
}

function handleContinue(): void {
  if (!canContinue.value) return
  if (!hasChanged.value) {
    emit('confirm', descriptionDraft.value.trim(), false, false)
    return
  }
  step.value = 'confirm'
}

function handleBack(): void {
  step.value = 'edit'
}

function handleConfirm(): void {
  emit('confirm', descriptionDraft.value.trim(), contractUpdateNeeded.value === 'yes', paymentUpdateNeeded.value === 'yes')
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    title="Change Scope"
    size="md"
    @update:model-value="emit('update:modelValue', $event)"
    @close="handleCancel"
  >
    <div v-if="step === 'edit'" class="flex flex-col gap-2">
      <p class="text-sm text-text-secondary">
        This is the project's scope-of-work description -- the same text shown as "What the Customer Asked For" on
        Overview.
      </p>
      <TextArea v-model="descriptionDraft" label="Scope of Work" :rows="6" />
    </div>

    <div v-else class="flex flex-col gap-5">
      <p class="text-sm text-text-secondary">
        The scope changed. Does this need a follow-up update in Contract or Payment? If both are "No", the scope is
        just saved as-is; otherwise every Administrator is notified to go make the update.
      </p>
      <RadioGroup v-model="contractUpdateNeeded" label="Does the Contract need to be updated?" :options="YES_NO_OPTIONS" :vertical="false" />
      <RadioGroup v-model="paymentUpdateNeeded" label="Does Payment need to be updated?" :options="YES_NO_OPTIONS" :vertical="false" />
    </div>

    <template #footer>
      <template v-if="step === 'edit'">
        <BaseButton variant="secondary" :disabled="isSubmitting" @click="handleCancel">Cancel</BaseButton>
        <BaseButton :disabled="!canContinue" @click="handleContinue">
          {{ hasChanged ? 'Continue' : 'Save' }}
        </BaseButton>
      </template>
      <template v-else>
        <BaseButton variant="secondary" :disabled="isSubmitting" @click="handleBack">Back</BaseButton>
        <BaseButton :loading="isSubmitting" @click="handleConfirm">Save Scope Change</BaseButton>
      </template>
    </template>
  </BaseDialog>
</template>
