<script setup lang="ts">
/**
 * A single-line, contenteditable text field for the template field
 * mapper. Behaves like a plain text input, except every `{{ token }}`
 * inside the value renders as a small, human-labelled, atomic chip
 * (e.g. "Client Name") instead of raw Jinja syntax -- and each chip
 * carries its own "x" to remove it in one click. This replaces the old
 * plain-<input> editor, where a placed field only ever showed up as
 * literal `{{ client_name }}` text buried in the document body,
 * indistinguishable from hand-typed prose and only removable by
 * carefully deleting the right characters by hand.
 *
 * The component owns HTML<->text conversion internally; callers only
 * ever see/set plain text (with `{{ }}` tokens) via `modelValue`, so
 * nothing else in the app needs to know chips exist.
 */
import { nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { MergeField } from '@/types/DocumentTemplate'

interface Props {
  modelValue: string
  fields: MergeField[]
  placeholder?: string
  /** The loop variable (e.g. "item", "term") of the field currently
   * flagged as this paragraph/row's repeating marker, if any. Any chip
   * belonging to that loop var -- the bare `{{ term }}` marker itself
   * for a repeating list, or any `{{ item.column }}` chip in a
   * repeating table's marked row -- renders with a distinct accent
   * style so it reads as "part of what repeats", not just another
   * chip. */
  repeatingLoopVar?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '',
  repeatingLoopVar: null,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  focus: []
  /** Fired when the user removes the chip that was flagged as this
   * block's repeating marker -- the parent owns that flag, so it has
   * to clear it too, not just the token text. */
  'remove-repeating': []
}>()

const { t } = useI18n()

const rootEl = ref<HTMLDivElement>()
const TOKEN_RE = /\{\{\s*([\w.]+)\s*\}\}/g

const CHIP_BASE_CLASSES =
  'inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2 py-0.5 align-baseline text-xs font-medium'
const CHIP_KNOWN_CLASSES = 'border-accent-300 bg-accent-100 text-accent-700'
const CHIP_REPEATING_CLASSES = 'border-accent-500 border-dashed bg-accent-200 text-accent-700'
const CHIP_UNKNOWN_CLASSES = 'border-warning-500/50 bg-warning-100 text-warning-700'
const CHIP_REMOVE_CLASSES =
  'flex h-3.5 w-3.5 items-center justify-center rounded-full leading-none opacity-60 hover:bg-black/10 hover:opacity-100'

let caretRange: Range | null = null
let suppressWatch = false

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

/** Human label for a token's inner expression -- "quotation_no" ->
 * "Quotation No.", "item.description" -> "Line Items: Description".
 * Falls back to the raw expression (flagged unknown) for a token that
 * doesn't match anything in the current field catalog -- e.g. one
 * hand-typed in Word, or left over from a document type change -- so
 * it stays visible rather than silently vanishing. */
function describeToken(expr: string): { label: string; known: boolean } {
  if (expr.includes('.')) {
    const [loopVar, columnKey] = expr.split('.')
    const field = props.fields.find((f) => f.kind === 'repeating_table' && f.loopVar === loopVar)
    const column = field?.columns?.find((c) => c.key === columnKey)
    if (field && column) return { label: `${field.label}: ${column.label}`, known: true }
    return { label: expr, known: false }
  }
  const textField = props.fields.find((f) => f.key === expr && f.kind === 'text')
  if (textField) return { label: textField.label, known: true }
  const listField = props.fields.find((f) => f.kind === 'repeating_list' && f.loopVar === expr)
  if (listField) return { label: listField.label, known: true }
  return { label: expr, known: false }
}

function exprLoopVar(expr: string): string {
  return expr.includes('.') ? expr.split('.')[0] : expr
}

function chipHtml(token: string): string {
  const expr = token.replace(/^\{\{\s*/, '').replace(/\s*\}\}$/, '')
  const { label, known } = describeToken(expr)
  const isRepeating = props.repeatingLoopVar != null && exprLoopVar(expr) === props.repeatingLoopVar
  const variantClasses = isRepeating ? CHIP_REPEATING_CLASSES : known ? CHIP_KNOWN_CLASSES : CHIP_UNKNOWN_CLASSES
  return (
    `<span class="${CHIP_BASE_CLASSES} ${variantClasses}" contenteditable="false" data-token="${escapeHtml(token)}">` +
    `<span>${escapeHtml(label)}</span>` +
    `<button type="button" class="${CHIP_REMOVE_CLASSES}" data-remove-token tabindex="-1" aria-label="${escapeHtml(t('administration.mergeField.remove', { label }))}">&times;</button>` +
    `</span>`
  )
}

function textToHtml(text: string): string {
  let html = ''
  let lastIndex = 0
  TOKEN_RE.lastIndex = 0
  let match: RegExpExecArray | null
  while ((match = TOKEN_RE.exec(text))) {
    html += escapeHtml(text.slice(lastIndex, match.index))
    html += chipHtml(match[0])
    lastIndex = match.index + match[0].length
  }
  html += escapeHtml(text.slice(lastIndex))
  return html
}

/** Reads the live DOM back into plain text -- text nodes contribute
 * their characters, a chip span contributes its stored raw token. */
function domToText(): string {
  const node = rootEl.value
  if (!node) return ''
  let out = ''
  for (const child of Array.from(node.childNodes)) {
    if (child.nodeType === Node.TEXT_NODE) {
      out += child.textContent ?? ''
    } else if (child instanceof HTMLElement && child.dataset.token) {
      out += child.dataset.token
    } else {
      out += child.textContent ?? ''
    }
  }
  return out
}

function render(): void {
  const node = rootEl.value
  if (!node) return
  node.innerHTML = textToHtml(props.modelValue)
}

onMounted(render)

watch(
  () => props.modelValue,
  () => {
    if (suppressWatch) {
      suppressWatch = false
      return
    }
    render()
  },
)

// Re-render on repeatingLoopVar changes too, so the accent style
// follows the flag (e.g. cleared elsewhere via the palette) without
// the user having to touch this field.
watch(() => props.repeatingLoopVar, render)

function emitFromDom(): void {
  suppressWatch = true
  emit('update:modelValue', domToText())
}

function captureCaret(): void {
  const sel = window.getSelection()
  if (!sel || sel.rangeCount === 0) return
  const range = sel.getRangeAt(0)
  if (rootEl.value && rootEl.value.contains(range.commonAncestorContainer)) {
    caretRange = range.cloneRange()
  }
}

function handleInput(): void {
  emitFromDom()
}

function handleFocus(): void {
  emit('focus')
  captureCaret()
}

function handleClick(event: MouseEvent): void {
  const target = event.target as HTMLElement
  const removeBtn = target.closest('[data-remove-token]') as HTMLElement | null
  if (removeBtn) {
    event.preventDefault()
    const chip = removeBtn.closest('[data-token]') as HTMLElement | null
    const token = chip?.dataset.token
    chip?.remove()
    emitFromDom()
    // Only a bare loop-var token (a repeating LIST's own marker, e.g.
    // "{{ term }}") auto-clears the flag on removal -- a repeating
    // TABLE's per-column tokens ("{{ item.description }}") don't,
    // since a row can hold several of those and removing one doesn't
    // mean the row should stop repeating; that's still the explicit
    // "Repeating: X" x-button's job.
    if (token) {
      const expr = token.replace(/^\{\{\s*/, '').replace(/\s*\}\}$/, '')
      if (expr === props.repeatingLoopVar) emit('remove-repeating')
    }
    return
  }
  captureCaret()
}

function handleKeyup(): void {
  captureCaret()
}

/** Inserts `token` (a `{{ ... }}` string) at the last known caret
 * position in this field -- called by the parent when the user clicks
 * a palette button. Falls back to appending at the end if no caret was
 * ever captured (e.g. the field was focused programmatically). */
async function insertToken(token: string): Promise<void> {
  const node = rootEl.value
  if (!node) return
  node.focus()

  const sel = window.getSelection()
  let range = caretRange
  if (!range || !node.contains(range.commonAncestorContainer)) {
    range = document.createRange()
    range.selectNodeContents(node)
    range.collapse(false)
  }
  sel?.removeAllRanges()
  sel?.addRange(range)

  range.deleteContents()
  const wrapper = document.createElement('span')
  wrapper.innerHTML = chipHtml(token)
  const chip = wrapper.firstElementChild as HTMLElement
  range.insertNode(chip)

  const after = document.createRange()
  after.setStartAfter(chip)
  after.collapse(true)
  sel?.removeAllRanges()
  sel?.addRange(after)
  caretRange = after.cloneRange()

  emitFromDom()
  await nextTick()
  node.focus()
}

defineExpose({ insertToken })
</script>

<template>
  <div
    ref="rootEl"
    class="min-h-9 w-full whitespace-pre-wrap break-words rounded-md border border-border-default bg-bg-card px-2.5 py-1.5 text-sm text-text-primary outline-none transition-colors duration-fast focus:border-accent-500 focus:ring-2 focus:ring-accent-500/30 empty:before:text-text-muted empty:before:content-[attr(aria-placeholder)]"
    contenteditable="true"
    role="textbox"
    :aria-placeholder="placeholder"
    @input="handleInput"
    @focus="handleFocus"
    @click="handleClick"
    @keyup="handleKeyup"
  />
</template>
