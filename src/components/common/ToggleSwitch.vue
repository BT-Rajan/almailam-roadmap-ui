<script setup lang="ts">
import { computed, useId } from 'vue'

import { useLocale } from '@/composables/useLocale'

interface Props {
  modelValue: boolean
  label?: string
  hint?: string
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  label: undefined,
  hint: undefined,
  disabled: false,
})

defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const toggleId = useId()
const { isRtl } = useLocale()

const toggleClasses = computed(() => [
  'relative h-6 w-11 shrink-0 rounded-full transition-colors duration-fast',
  'peer-focus-visible:ring-2 peer-focus-visible:ring-accent-500/30 peer-focus-visible:ring-offset-2',
  props.modelValue ? 'bg-primary-500' : 'bg-neutral-300',
  props.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
])

// The thumb rests at its static position (the inline-start edge, which
// flips sides for free under dir="rtl") and slides toward the
// inline-end edge when on. translateX moves along the physical X axis
// regardless of writing direction, so the "on" offset has to flip sign
// in RTL to still mean "toward the end edge" rather than "further past
// the start edge". Written as literal class names (not built from a
// template string) so Tailwind's build-time scanner can find them.
const thumbClasses = computed(() => {
  const base = 'h-5 w-5 rounded-full bg-white transition-transform duration-fast absolute top-0.5'
  if (props.modelValue) {
    return [base, isRtl.value ? '-translate-x-5' : 'translate-x-5']
  }
  return [base, isRtl.value ? '-translate-x-0.5' : 'translate-x-0.5']
})
</script>

<template>
  <label
    :for="toggleId"
    class="flex items-start gap-3"
    :class="disabled ? 'cursor-not-allowed' : 'cursor-pointer'"
  >
    <span class="flex items-center">
      <input
        :id="toggleId"
        type="checkbox"
        :checked="modelValue"
        :disabled="disabled"
        class="peer sr-only"
        @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
      />
      <span :class="toggleClasses">
        <span :class="thumbClasses" />
      </span>
    </span>
    <span v-if="label || hint" class="flex flex-col gap-0.5">
      <span class="text-sm font-medium text-text-secondary" :class="disabled ? 'text-text-muted' : ''">
        {{ label }}
      </span>
      <span v-if="hint" class="text-xs text-text-muted">{{ hint }}</span>
    </span>
  </label>
</template>
