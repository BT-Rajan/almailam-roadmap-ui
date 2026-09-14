<script setup lang="ts">
import { X } from '@lucide/vue'
import { computed, ref, useId } from 'vue'
import { useI18n } from 'vue-i18n'

import { validators } from '@/utils/validators'

const props = withDefaults(
  defineProps<{
    modelValue: string[]
    label?: string
    hint?: string
    placeholder?: string
    max?: number
    error?: string
    required?: boolean
  }>(),
  {
    label: undefined,
    hint: undefined,
    placeholder: undefined,
    max: 5,
    error: undefined,
    required: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string[]]
}>()

const { t } = useI18n()
const inputId = useId()
const draft = ref('')
const draftError = ref<string>()

const atLimit = computed(() => props.modelValue.length >= props.max)

// Each address becomes its own removable chip on Enter/comma/blur --
// rather than one free-text box the person has to get the separators
// right in (the recipients field this replaces was a plain textarea
// split on newlines/commas at submit time, with no feedback on a typo'd
// address until the send actually failed) -- and the count is capped
// right here rather than only caught by the backend after submit.
function tryAdd(rawValue: string): void {
  const address = rawValue.trim().replace(/,$/, '')
  if (!address) return
  if (atLimit.value) {
    draftError.value = t('common.emailListInput.limitReached', { max: props.max })
    return
  }
  const check = validators.email()(address)
  if (check !== true) {
    draftError.value = typeof check === 'string' ? check : undefined
    return
  }
  if (props.modelValue.some((existing) => existing.toLowerCase() === address.toLowerCase())) {
    draftError.value = t('common.emailListInput.duplicate')
    return
  }
  emit('update:modelValue', [...props.modelValue, address])
  draft.value = ''
  draftError.value = undefined
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter' || event.key === ',') {
    event.preventDefault()
    tryAdd(draft.value)
  } else if (event.key === 'Backspace' && draft.value === '' && props.modelValue.length > 0) {
    removeAt(props.modelValue.length - 1)
  }
}

function handleBlur(): void {
  if (draft.value.trim()) tryAdd(draft.value)
}

function removeAt(index: number): void {
  const next = [...props.modelValue]
  next.splice(index, 1)
  emit('update:modelValue', next)
  draftError.value = undefined
}
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="inputId" class="text-sm font-medium text-text-secondary">
      {{ label }}
      <span v-if="required" class="text-danger-500">*</span>
      <span class="ms-1 font-normal text-text-muted">({{ modelValue.length }}/{{ max }})</span>
    </label>
    <div
      class="flex flex-wrap items-center gap-1.5 rounded-lg border bg-bg-card p-2 transition-colors duration-fast"
      :class="error || draftError ? 'border-danger-500' : 'border-border-default focus-within:border-accent-500'"
    >
      <span
        v-for="(address, index) in modelValue"
        :key="address"
        class="inline-flex items-center gap-1 rounded-md bg-bg-secondary px-2 py-1 text-xs text-text-primary"
      >
        {{ address }}
        <button type="button" class="text-text-muted hover:text-danger-500" @click="removeAt(index)">
          <X class="h-3 w-3" />
        </button>
      </span>
      <input
        :id="inputId"
        v-model="draft"
        type="email"
        :placeholder="modelValue.length === 0 ? placeholder : ''"
        :disabled="atLimit"
        class="min-w-[10rem] flex-1 border-none bg-transparent p-1 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-0 disabled:cursor-not-allowed"
        @keydown="handleKeydown"
        @blur="handleBlur"
      />
    </div>
    <p v-if="error" class="text-xs text-danger-500">{{ error }}</p>
    <p v-else-if="draftError" class="text-xs text-danger-500">{{ draftError }}</p>
    <p v-else-if="atLimit" class="text-xs text-warning-700">{{ t('common.emailListInput.limitReached', { max }) }}</p>
    <p v-else-if="hint" class="text-xs text-text-muted">{{ hint }}</p>
  </div>
</template>
