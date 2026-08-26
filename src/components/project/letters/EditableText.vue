<script setup lang="ts">
/**
 * A single piece of a lettered template that isn't sourced from another
 * DB record (Client/Project) -- it's free text specific to this one
 * document. Renders as plain text; becomes a contenteditable region
 * (with a visible focus ring) while the letter is still a draft, and
 * emits the new value on blur so the parent can persist it.
 */
import { onMounted, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: string
    editable: boolean
    placeholder?: string
    multiline?: boolean
    /** What this field actually is (e.g. "Client representative name") --
     * without this, a contenteditable region has no accessible name at
     * all, since it isn't a real form control a <label> can point to. */
    ariaLabel?: string
  }>(),
  { placeholder: '—', multiline: false, ariaLabel: undefined },
)

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const elementRef = ref<HTMLElement>()

function currentText(): string {
  return props.modelValue || props.placeholder
}

// contenteditable is an *enumerated* HTML attribute expecting the
// literal strings "true"/"false", not a real boolean attribute -- binding
// a raw JS boolean to it is a well-known Vue gotcha that silently fails
// to make the element editable in some cases, so this is explicit.
function contentEditableAttr(): 'true' | 'false' {
  return props.editable ? 'true' : 'false'
}

onMounted(() => {
  if (elementRef.value) elementRef.value.textContent = currentText()
})

// The element's own DOM text is the source of truth while the user is
// typing. Only overwrite it from an external prop change (another field
// saving elsewhere on the page causes the whole document to re-render)
// when this field isn't the one currently focused -- otherwise every
// unrelated save would reset whatever the user is mid-typing here.
watch(
  () => props.modelValue,
  () => {
    if (!elementRef.value) return
    if (document.activeElement === elementRef.value) return
    elementRef.value.textContent = currentText()
  },
)

function onBlur(event: FocusEvent): void {
  const target = event.target as HTMLElement
  const value = (target.innerText ?? '').trim()
  emit('update:modelValue', value)
}
</script>

<template>
  <component
    :is="multiline ? 'div' : 'span'"
    ref="elementRef"
    :contenteditable="contentEditableAttr()"
    class="outline-none"
    :class="editable ? 'rounded px-0.5 hover:bg-amber-50 focus:bg-amber-50 focus:ring-1 focus:ring-amber-400 print:hover:bg-transparent print:focus:ring-0' : ''"
    :role="editable ? 'textbox' : undefined"
    :aria-label="editable ? ariaLabel : undefined"
    :aria-multiline="editable && multiline ? 'true' : undefined"
    @blur="onBlur"
  />
</template>
