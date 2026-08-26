<script setup lang="ts">
import { Plus, X } from '@lucide/vue'

/**
 * A bulleted list of free-text lines specific to this one document
 * (scope-of-work items, payment milestones). An item starting with
 * "## " renders as a section heading instead of a bullet -- used for
 * the phase headings inside the scope box (e.g. "Phase 1 (Design)").
 * Editable mode adds add/remove controls; the print/read view shows
 * plain text only.
 */
const props = defineProps<{
  modelValue: string[]
  editable: boolean
}>()

const emit = defineEmits<{ 'update:modelValue': [value: string[]] }>()

function isHeading(item: string): boolean {
  return item.startsWith('## ')
}

function headingText(item: string): string {
  return item.slice(3)
}

function updateItem(index: number, text: string, heading: boolean): void {
  const next = [...props.modelValue]
  next[index] = heading ? `## ${text}` : text
  emit('update:modelValue', next)
}

function removeItem(index: number): void {
  emit(
    'update:modelValue',
    props.modelValue.filter((_, i) => i !== index),
  )
}

function addLine(): void {
  emit('update:modelValue', [...props.modelValue, ''])
}

function addHeading(): void {
  emit('update:modelValue', [...props.modelValue, '## '])
}

// A local directive (auto-registered by the vXxx naming convention in
// <script setup>) that sets the element's text on mount/update, but
// skips the update while the element is the one currently focused --
// otherwise an unrelated save elsewhere on the page (which re-renders
// this whole list from the server response) would reset whatever the
// user is mid-typing in this particular line.
function vEditableText(el: HTMLElement, binding: { value: string }): void {
  if (document.activeElement === el) return
  el.textContent = binding.value
}
</script>

<template>
  <ul class="space-y-1">
    <li
      v-for="(item, index) in modelValue"
      :key="index"
      class="group flex items-start gap-2"
      :class="isHeading(item) ? 'mt-2 font-semibold' : 'ps-4'"
    >
      <span v-if="!isHeading(item)" class="select-none" aria-hidden="true">•</span>
      <span
        v-editable-text="isHeading(item) ? headingText(item) : item"
        class="flex-1 outline-none"
        :contenteditable="editable ? 'true' : 'false'"
        :class="editable ? 'rounded px-0.5 hover:bg-amber-50 focus:bg-amber-50 focus:ring-1 focus:ring-amber-400 print:hover:bg-transparent print:focus:ring-0' : ''"
        :role="editable ? 'textbox' : undefined"
        :aria-label="editable ? (isHeading(item) ? `Heading ${index + 1}` : `List item ${index + 1}`) : undefined"
        :aria-multiline="editable ? 'false' : undefined"
        @blur="(e) => updateItem(index, (e.target as HTMLElement).innerText.trim(), isHeading(item))"
      />
      <button
        v-if="editable"
        type="button"
        class="no-print opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100 focus-visible:opacity-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500"
        :aria-label="`Remove line ${index + 1}`"
        @click="removeItem(index)"
      >
        <X class="h-3.5 w-3.5 text-slate-400 hover:text-red-500" />
      </button>
    </li>
  </ul>
  <div v-if="editable" class="no-print mt-2 flex gap-3 text-xs">
    <button type="button" class="flex items-center gap-1 text-teal-700 hover:text-teal-900" @click="addLine">
      <Plus class="h-3.5 w-3.5" /> Add line
    </button>
    <button type="button" class="flex items-center gap-1 text-slate-500 hover:text-slate-700" @click="addHeading">
      <Plus class="h-3.5 w-3.5" /> Add heading
    </button>
  </div>
</template>
