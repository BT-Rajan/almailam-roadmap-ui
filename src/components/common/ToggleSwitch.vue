<script setup lang="ts">
import { computed, useId } from 'vue'

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

const toggleClasses = computed(() => [
  'h-6 w-11 rounded-full transition-colors duration-fast',
  props.modelValue ? 'bg-primary-500' : 'bg-neutral-300',
  props.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer',
])

const thumbClasses = computed(() => [
  'h-5 w-5 rounded-full bg-white transition-transform duration-fast absolute top-0.5',
  props.modelValue ? 'translate-x-5' : 'translate-x-0.5',
])
</script>

<template>
  <div class="flex items-start gap-3">
    <div class="flex items-center">
      <input
        :id="toggleId"
        type="checkbox"
        :checked="modelValue"
        :disabled="disabled"
        class="sr-only"
        @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
      />
      <div :class="toggleClasses">
        <div :class="thumbClasses" />
      </div>
    </div>
    <div v-if="label || hint" class="flex flex-col gap-0.5">
      <label :for="toggleId" class="text-sm font-medium text-neutral-700 cursor-pointer" :class="disabled ? 'text-neutral-400' : ''">
        {{ label }}
      </label>
      <p v-if="hint" class="text-xs text-neutral-400">{{ hint }}</p>
    </div>
  </div>
</template>
