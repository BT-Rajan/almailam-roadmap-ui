<script setup lang="ts">
import { Bold, ImagePlus, Italic, Underline } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, ref, useId, watch } from 'vue'

import { sanitizeHtml } from '@/utils/sanitizeHtml'

interface Props {
  modelValue: string
  label?: string
  placeholder?: string
  hint?: string
  error?: string
  required?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  label: undefined,
  placeholder: 'Start typing...',
  hint: undefined,
  error: undefined,
  required: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const FONT_SIZES = [
  { label: 'Small', value: '12' },
  { label: 'Normal', value: '14' },
  { label: 'Medium', value: '18' },
  { label: 'Large', value: '24' },
  { label: 'X-Large', value: '32' },
]

// A file this size, base64-encoded, comfortably fits the MEDIUMTEXT
// columns these fields save into (see backend migration 0055) even
// alongside the rest of a long clause or notes field.
const MAX_IMAGE_BYTES = 1.5 * 1024 * 1024

const editorId = useId()
const editorRef = ref<HTMLDivElement | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)
const imageError = ref('')

// Toolbar controls (a font-size <select>, a file <input>) necessarily
// steal focus away from the contenteditable, which would otherwise lose
// the user's text selection before a command can be applied to it. This
// tracks the live selection while it's inside the editor so it can be
// restored right before running a command.
let savedRange: Range | null = null

function trackSelection(): void {
  const selection = window.getSelection()
  if (!selection || selection.rangeCount === 0) return
  const range = selection.getRangeAt(0)
  if (editorRef.value?.contains(range.commonAncestorContainer)) {
    savedRange = range.cloneRange()
  }
}

function restoreSelection(): void {
  const editor = editorRef.value
  if (!editor) return
  editor.focus()
  const selection = window.getSelection()
  if (!selection || !savedRange) return
  selection.removeAllRanges()
  selection.addRange(savedRange)
}

onMounted(() => {
  if (editorRef.value) editorRef.value.innerHTML = props.modelValue || ''
  document.addEventListener('selectionchange', trackSelection)
})

onBeforeUnmount(() => {
  document.removeEventListener('selectionchange', trackSelection)
})

// Only re-sync from an external modelValue change (switching drafts,
// Cancel resetting the form) -- never while this editor itself has
// focus, or every keystroke's own emit would immediately overwrite the
// DOM out from under the caret.
watch(
  () => props.modelValue,
  (value) => {
    const editor = editorRef.value
    if (!editor || document.activeElement === editor) return
    if (editor.innerHTML !== (value || '')) {
      editor.innerHTML = value || ''
    }
  },
)

function handleInput(): void {
  const editor = editorRef.value
  if (!editor) return
  emit('update:modelValue', sanitizeHtml(editor.innerHTML))
}

function applyCommand(command: 'bold' | 'italic' | 'underline'): void {
  restoreSelection()
  document.execCommand(command)
  handleInput()
}

function applyFontSize(event: Event): void {
  const select = event.target as HTMLSelectElement
  const px = select.value
  select.value = ''
  if (!px || !savedRange || savedRange.collapsed) return
  restoreSelection()
  const span = document.createElement('span')
  span.style.fontSize = `${px}px`
  span.appendChild(savedRange.extractContents())
  savedRange.insertNode(span)
  const selection = window.getSelection()
  if (selection) {
    selection.removeAllRanges()
    const range = document.createRange()
    range.selectNodeContents(span)
    selection.addRange(range)
    savedRange = range.cloneRange()
  }
  handleInput()
}

function triggerImagePicker(): void {
  imageError.value = ''
  fileInputRef.value?.click()
}

function handleImageSelected(event: Event): void {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (!file.type.startsWith('image/')) {
    imageError.value = 'Please choose an image file.'
    return
  }
  if (file.size > MAX_IMAGE_BYTES) {
    imageError.value = 'Image is too large -- please use one under 1.5MB.'
    return
  }
  imageError.value = ''
  const reader = new FileReader()
  reader.onload = () => {
    restoreSelection()
    document.execCommand('insertHTML', false, `<img src="${reader.result}" alt="" />`)
    handleInput()
  }
  reader.readAsDataURL(file)
}

const wrapperClasses = computed(() => [
  'w-full rounded-lg border bg-bg-card text-sm text-text-primary',
  'transition-colors duration-fast focus-within:ring-2 focus-within:ring-accent-500/30',
  props.error ? 'border-danger-500' : 'border-border-default focus-within:border-accent-500',
])
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="editorId" class="text-sm font-medium text-text-secondary">
      {{ label }}
      <span v-if="required" class="text-danger-500">*</span>
    </label>
    <div :class="wrapperClasses">
      <div class="no-print flex flex-wrap items-center gap-1 border-b border-border-light p-1.5">
        <button
          type="button"
          class="flex h-8 w-8 items-center justify-center rounded-md text-text-muted transition-colors duration-fast hover:bg-bg-hover hover:text-text-primary"
          title="Bold"
          aria-label="Bold"
          @mousedown.prevent
          @click="applyCommand('bold')"
        >
          <Bold class="h-4 w-4" />
        </button>
        <button
          type="button"
          class="flex h-8 w-8 items-center justify-center rounded-md text-text-muted transition-colors duration-fast hover:bg-bg-hover hover:text-text-primary"
          title="Italic"
          aria-label="Italic"
          @mousedown.prevent
          @click="applyCommand('italic')"
        >
          <Italic class="h-4 w-4" />
        </button>
        <button
          type="button"
          class="flex h-8 w-8 items-center justify-center rounded-md text-text-muted transition-colors duration-fast hover:bg-bg-hover hover:text-text-primary"
          title="Underline"
          aria-label="Underline"
          @mousedown.prevent
          @click="applyCommand('underline')"
        >
          <Underline class="h-4 w-4" />
        </button>
        <div class="mx-1 h-5 w-px bg-border-light" />
        <select
          class="h-8 rounded-md border border-border-default bg-bg-card px-1.5 text-xs text-text-secondary"
          title="Font size (select text first)"
          aria-label="Font size"
          @mousedown="trackSelection"
          @change="applyFontSize"
        >
          <option value="">Font Size</option>
          <option v-for="size in FONT_SIZES" :key="size.value" :value="size.value">{{ size.label }}</option>
        </select>
        <div class="mx-1 h-5 w-px bg-border-light" />
        <button
          type="button"
          class="flex h-8 w-8 items-center justify-center rounded-md text-text-muted transition-colors duration-fast hover:bg-bg-hover hover:text-text-primary"
          title="Insert Image"
          aria-label="Insert Image"
          @mousedown.prevent
          @click="triggerImagePicker"
        >
          <ImagePlus class="h-4 w-4" />
        </button>
        <input ref="fileInputRef" type="file" accept="image/*" class="hidden" @change="handleImageSelected" />
      </div>
      <div
        :id="editorId"
        ref="editorRef"
        class="rich-text-content min-h-[6rem] p-3 focus:outline-none"
        contenteditable="true"
        :data-placeholder="placeholder"
        :aria-invalid="Boolean(error)"
        :aria-describedby="error ? `${editorId}-error` : hint ? `${editorId}-hint` : undefined"
        @input="handleInput"
      />
    </div>
    <p v-if="imageError" class="text-xs text-danger-500">{{ imageError }}</p>
    <p v-if="error" :id="`${editorId}-error`" class="text-xs text-danger-500">{{ error }}</p>
    <p v-else-if="hint" :id="`${editorId}-hint`" class="text-xs text-text-muted">{{ hint }}</p>
  </div>
</template>

<style scoped>
[contenteditable]:empty:before {
  content: attr(data-placeholder);
  color: var(--color-text-muted);
}
</style>
