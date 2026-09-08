<script setup lang="ts">
import { computed, nextTick, onMounted, ref, useId, watch } from 'vue'

interface Props {
  modelValue: string
  label?: string
  placeholder?: string
  hint?: string
  error?: string
  disabled?: boolean
  required?: boolean
  rows?: number
  maxLength?: number
}

const props = withDefaults(defineProps<Props>(), {
  label: undefined,
  placeholder: undefined,
  hint: undefined,
  error: undefined,
  disabled: false,
  required: false,
  rows: 4,
  maxLength: undefined,
})

defineEmits<{
  'update:modelValue': [value: string]
}>()

const textareaId = useId()
const textareaEl = ref<HTMLTextAreaElement>()
// The browser's own `rows`-driven height, captured once before any
// inline height override exists -- resize() below floors to this so a
// short value (e.g. one line in a `rows="3"` field) still shows the
// full 3 rows of empty space rather than collapsing to fit just that
// one line.
let minHeightPx = 0

// Grows with content instead of clipping it behind a scrollbar inside
// a fixed-height box (rows is still the starting/minimum height, e.g.
// for an auto-filled Scope of Work that can run well past it) --
// resetting to 'auto' first is required so scrollHeight reflects a
// shrink back toward minHeightPx too, not just growth. Capped by the
// max-h-[60vh] class below (overflow-y-auto beyond that) so genuinely
// huge content can't push the rest of the page/dialog off-screen;
// ordinary content never gets near that cap.
function resize(): void {
  const el = textareaEl.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.max(el.scrollHeight, minHeightPx)}px`
}

watch(() => props.modelValue, () => nextTick(resize))
onMounted(() => {
  if (textareaEl.value) minHeightPx = textareaEl.value.offsetHeight
  resize()
})

const textareaClasses = computed(() => [
  'w-full rounded-lg border bg-bg-card text-sm text-text-primary p-3',
  'placeholder:text-text-muted',
  'transition-colors duration-fast',
  'focus:outline-none focus:ring-2 focus:ring-accent-500/30',
  'resize-none overflow-y-auto max-h-[60vh]',
  props.error ? 'border-danger-500' : 'border-border-default focus:border-accent-500',
  props.disabled ? 'cursor-not-allowed bg-bg-secondary text-text-muted' : '',
])

const charCount = computed(() => `${props.modelValue.length}${props.maxLength ? `/${props.maxLength}` : ''}`)
</script>

<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" :for="textareaId" class="text-sm font-medium text-text-secondary">
      {{ label }}
      <span v-if="required" class="text-danger-500">*</span>
    </label>
    <textarea
      :id="textareaId"
      ref="textareaEl"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :rows="rows"
      :maxlength="maxLength"
      :class="textareaClasses"
      :aria-invalid="Boolean(error)"
      :aria-describedby="error ? `${textareaId}-error` : hint ? `${textareaId}-hint` : undefined"
      @input="
        $emit('update:modelValue', ($event.target as HTMLTextAreaElement).value);
        resize()
      "
    />
    <div class="flex items-center justify-between gap-2">
      <div>
        <p v-if="error" :id="`${textareaId}-error`" class="text-xs text-danger-500">{{ error }}</p>
        <p v-else-if="hint" :id="`${textareaId}-hint`" class="text-xs text-text-muted">{{ hint }}</p>
      </div>
      <p v-if="maxLength" class="text-xs text-text-muted">{{ charCount }}</p>
    </div>
  </div>
</template>
