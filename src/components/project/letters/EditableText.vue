<script setup lang="ts">
/**
 * A single piece of a lettered template that isn't sourced from another
 * DB record (Client/Project) -- it's free text specific to this one
 * document. Renders as plain text; becomes a contenteditable region
 * (with a visible focus ring) while the letter is still a draft, and
 * emits the new value on blur so the parent can persist it.
 */
withDefaults(
  defineProps<{
    modelValue: string
    editable: boolean
    placeholder?: string
    multiline?: boolean
  }>(),
  { placeholder: '—', multiline: false },
)

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

function onBlur(event: FocusEvent): void {
  const target = event.target as HTMLElement
  const value = (target.innerText ?? '').trim()
  emit('update:modelValue', value)
}
</script>

<template>
  <component
    :is="multiline ? 'div' : 'span'"
    :contenteditable="editable"
    class="outline-none"
    :class="editable ? 'rounded px-0.5 hover:bg-amber-50 focus:bg-amber-50 focus:ring-1 focus:ring-amber-400 print:hover:bg-transparent print:focus:ring-0' : ''"
    @blur="onBlur"
    >{{ modelValue || placeholder }}</component
  >
</template>
