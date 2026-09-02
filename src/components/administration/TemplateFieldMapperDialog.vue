<script setup lang="ts">
import { X } from '@lucide/vue'
import { nextTick, ref, watch } from 'vue'

import BaseDialog from '@/components/common/BaseDialog.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import { documentTemplateService } from '@/services/documentTemplateService'
import { useToastStore } from '@/stores/toastStore'
import type { DocumentTemplate, MergeField, TemplateBlock } from '@/types/DocumentTemplate'

interface Props {
  modelValue: boolean
  template: DocumentTemplate | undefined
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: []
}>()

const toastStore = useToastStore()

const isLoading = ref(false)
const isSaving = ref(false)
const loadError = ref('')
const mergeFields = ref<MergeField[]>([])
const blocks = ref<TemplateBlock[]>([])

// Which input the last "insert field" click should target -- set by
// every paragraph/cell input's own @focus handler. Kept as a plain
// (non-reactive) object holding the live element, not a ref to a
// Vue-tracked value, since what's inserted needs the DOM's own current
// selectionStart/selectionEnd (cursor position), which Vue's reactivity
// has no notion of.
type FocusTarget =
  | { kind: 'paragraph'; blockIndex: number; el: HTMLInputElement }
  | { kind: 'cell'; blockIndex: number; rowIndex: number; cellIndex: number; el: HTMLInputElement }
let focusTarget: FocusTarget | null = null

function setFocus(target: FocusTarget): void {
  focusTarget = target
}

watch(
  () => props.modelValue,
  async (isOpen) => {
    if (!isOpen || !props.template) return
    isLoading.value = true
    loadError.value = ''
    blocks.value = []
    focusTarget = null
    try {
      const [fields, layout] = await Promise.all([
        documentTemplateService.getMergeFields(props.template.documentType),
        documentTemplateService.getTemplateLayout(props.template.id),
      ])
      mergeFields.value = fields
      // Structured-cloned so editing here never mutates the fetched
      // layout in place -- irrelevant today (nothing else reads it),
      // but a stray shared-reference bug in an editor like this is the
      // kind of thing that's invisible until two dialogs interact.
      blocks.value = structuredClone(layout.blocks)
    } catch (error) {
      loadError.value = error instanceof Error ? error.message : 'Failed to load this template.'
    } finally {
      isLoading.value = false
    }
  },
)

function textFields(): MergeField[] {
  return mergeFields.value.filter((f) => f.kind === 'text')
}
function repeatingTableFields(): MergeField[] {
  return mergeFields.value.filter((f) => f.kind === 'repeating_table')
}
function repeatingListFields(): MergeField[] {
  return mergeFields.value.filter((f) => f.kind === 'repeating_list')
}

function fieldLabel(key: string): string {
  return mergeFields.value.find((f) => f.key === key)?.label ?? key
}

/** Unsets `fieldKey` from wherever it's currently flagged -- a
 * repeating field can only occupy one paragraph/row at a time (that's
 * what makes its for/endfor markers unambiguous to place), so marking a
 * new location always displaces the old one. */
function clearRepeatingField(fieldKey: string): void {
  for (const block of blocks.value) {
    if (block.kind === 'paragraph' && block.repeatingField === fieldKey) {
      block.repeatingField = null
    } else if (block.kind === 'table') {
      for (const row of block.rows ?? []) {
        if (row.repeatingField === fieldKey) row.repeatingField = null
      }
    }
  }
}

function insertToken(token: string, markRepeatingField?: string): void {
  if (!focusTarget) return
  const target = focusTarget
  const el = target.el
  const start = el.selectionStart ?? el.value.length
  const end = el.selectionEnd ?? el.value.length
  const newValue = el.value.slice(0, start) + token + el.value.slice(end)

  const block = blocks.value.find((b) => b.blockIndex === target.blockIndex)
  if (!block) return

  if (target.kind === 'paragraph' && block.kind === 'paragraph') {
    block.text = newValue
    if (markRepeatingField) {
      clearRepeatingField(markRepeatingField)
      block.repeatingField = markRepeatingField
    }
  } else if (target.kind === 'cell' && block.kind === 'table') {
    const row = block.rows?.find((r) => r.rowIndex === target.rowIndex)
    const cell = row?.cells.find((c) => c.cellIndex === target.cellIndex)
    if (!row || !cell) return
    cell.text = newValue
    if (markRepeatingField) {
      clearRepeatingField(markRepeatingField)
      row.repeatingField = markRepeatingField
    }
  }

  const cursorPosition = start + token.length
  nextTick(() => {
    el.focus()
    el.setSelectionRange(cursorPosition, cursorPosition)
  })
}

function clearRowRepeating(row: { repeatingField: string | null }): void {
  row.repeatingField = null
}
function clearParagraphRepeating(block: TemplateBlock): void {
  block.repeatingField = null
}

async function handleSave(): Promise<void> {
  if (!props.template) return
  isSaving.value = true
  try {
    await documentTemplateService.saveTemplateMapping(props.template.id, blocks.value)
    toastStore.show('success', 'Fields mapped', `${props.template.originalFilename} was updated.`)
    emit('saved')
    emit('update:modelValue', false)
  } catch (error) {
    toastStore.show('error', 'Could not save mapping', error instanceof Error ? error.message : 'Please try again.')
  } finally {
    isSaving.value = false
  }
}

function handleClose(): void {
  if (isSaving.value) return
  emit('update:modelValue', false)
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="`Map Fields -- ${template?.originalFilename ?? ''}`"
    size="lg"
    :closable="!isSaving"
    @update:model-value="handleClose"
  >
    <SkeletonLoader v-if="isLoading" :rows="6" />
    <p v-else-if="loadError" class="text-sm text-danger-600">{{ loadError }}</p>

    <div v-else class="flex flex-col gap-5">
      <p class="text-xs text-text-muted">
        Click into a line of the document below, then click a field to insert it at that spot. For a repeating
        table (e.g. line items), click into the row that should repeat, then click each column into its cell.
      </p>

      <!-- Field palette -->
      <div class="flex flex-col gap-3 rounded-lg border border-border-light bg-bg-secondary p-3">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="field in textFields()"
            :key="field.key"
            type="button"
            class="rounded-full border border-border-default bg-bg-card px-3 py-1 text-xs font-medium text-text-secondary transition-colors duration-fast hover:border-accent-500 hover:text-accent-600"
            @click="insertToken(`{{ ${field.key} }}`)"
          >
            {{ field.label }}
          </button>
        </div>

        <div v-for="field in repeatingTableFields()" :key="field.key" class="flex flex-col gap-1.5 border-t border-border-light pt-3">
          <p class="text-xs text-text-muted">{{ field.label }} columns -- click into a table cell first:</p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="column in field.columns"
              :key="column.key"
              type="button"
              :disabled="focusTarget?.kind !== 'cell'"
              class="rounded-full border border-border-default bg-bg-card px-3 py-1 text-xs font-medium text-text-secondary transition-colors duration-fast hover:border-accent-500 hover:text-accent-600 disabled:cursor-not-allowed disabled:opacity-40"
              @click="insertToken(`{{ ${field.loopVar}.${column.key} }}`, field.key)"
            >
              {{ column.label }}
            </button>
          </div>
        </div>

        <div v-for="field in repeatingListFields()" :key="field.key" class="flex flex-col gap-1.5 border-t border-border-light pt-3">
          <p class="text-xs text-text-muted">{{ field.label }} -- click into the line that should repeat first:</p>
          <button
            type="button"
            :disabled="focusTarget?.kind !== 'paragraph'"
            class="w-fit rounded-full border border-border-default bg-bg-card px-3 py-1 text-xs font-medium text-text-secondary transition-colors duration-fast hover:border-accent-500 hover:text-accent-600 disabled:cursor-not-allowed disabled:opacity-40"
            @click="insertToken(`{{ ${field.loopVar} }}`, field.key)"
          >
            {{ field.label }}
          </button>
        </div>
      </div>

      <!-- Document body -->
      <div class="flex max-h-[50vh] flex-col gap-3 overflow-y-auto rounded-lg border border-border-light p-3">
        <template v-for="block in blocks" :key="`${block.kind}-${block.blockIndex}`">
          <input
            v-if="block.kind === 'paragraph'"
            v-model="block.text"
            type="text"
            class="h-9 w-full rounded-md border bg-bg-card px-2.5 text-sm text-text-primary transition-colors duration-fast focus:outline-none focus:ring-2 focus:ring-accent-500/30"
            :class="block.repeatingField ? 'border-accent-500' : 'border-border-default focus:border-accent-500'"
            @focus="setFocus({ kind: 'paragraph', blockIndex: block.blockIndex, el: $event.target as HTMLInputElement })"
          />
          <div v-if="block.kind === 'paragraph' && block.repeatingField" class="-mt-2 flex items-center gap-1 text-[11px] text-accent-600">
            <span>Repeating: {{ fieldLabel(block.repeatingField) }}</span>
            <button type="button" class="hover:text-accent-700" @click="clearParagraphRepeating(block)">
              <X class="h-3 w-3" />
            </button>
          </div>

          <div v-if="block.kind === 'table'" class="overflow-x-auto">
            <table class="w-full border-collapse text-sm">
              <tbody>
                <tr v-for="row in block.rows" :key="row.rowIndex">
                  <td v-for="cell in row.cells" :key="cell.cellIndex" class="border border-border-light p-1">
                    <input
                      v-model="cell.text"
                      type="text"
                      class="h-9 w-full min-w-[8rem] rounded-md border bg-bg-card px-2 text-sm text-text-primary transition-colors duration-fast focus:outline-none focus:ring-2 focus:ring-accent-500/30"
                      :class="row.repeatingField ? 'border-accent-500' : 'border-border-default focus:border-accent-500'"
                      @focus="
                        setFocus({
                          kind: 'cell',
                          blockIndex: block.blockIndex,
                          rowIndex: row.rowIndex,
                          cellIndex: cell.cellIndex,
                          el: $event.target as HTMLInputElement,
                        })
                      "
                    />
                  </td>
                  <td v-if="row.repeatingField" class="whitespace-nowrap p-1 text-[11px] text-accent-600">
                    <span class="inline-flex items-center gap-1">
                      Repeating: {{ fieldLabel(row.repeatingField) }}
                      <button type="button" class="hover:text-accent-700" @click="clearRowRepeating(row)">
                        <X class="h-3 w-3" />
                      </button>
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </div>
    </div>

    <template #footer>
      <FormActionBar submit-label="Save Mapping" :disabled="isLoading || Boolean(loadError)" :loading="isSaving" @submit="handleSave" @cancel="handleClose" />
    </template>
  </BaseDialog>
</template>
