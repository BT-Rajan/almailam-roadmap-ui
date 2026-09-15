<script setup lang="ts">
import { ArrowLeft, ArrowRight, CornerDownLeft, CornerDownRight, Repeat, X } from '@lucide/vue'
import { computed, nextTick, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import BaseButton from '@/components/common/BaseButton.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import FormActionBar from '@/components/common/FormActionBar.vue'
import SearchBox from '@/components/common/SearchBox.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import MergeFieldRichInput from '@/components/administration/MergeFieldRichInput.vue'
import { useLocale } from '@/composables/useLocale'
import { ROUTE_NAMES } from '@/constants/routeNames'
import { documentTemplateService } from '@/services/documentTemplateService'
import { useDocumentTemplateStore } from '@/stores/documentTemplateStore'
import { useToastStore } from '@/stores/toastStore'
import type { MergeField, TemplateBlock, TemplateRow } from '@/types/DocumentTemplate'

// Replaces TemplateFieldMapperDialog.vue's modal -- a dedicated route
// (/admin/documents/templates/:templateId/fields). No 'new' sentinel
// like UserFormPage/ScheduledReportFormPage: a template always exists
// first (uploaded via DocumentTemplatesPanel.vue) before its fields can
// be mapped, so this only ever edits one that's already there -- if
// :templateId doesn't resolve, that's a genuine not-found, not a
// create mode.

const route = useRoute()
const router = useRouter()
const toastStore = useToastStore()
const documentTemplateStore = useDocumentTemplateStore()
const { t } = useI18n()
const { isRtl } = useLocale()

const backIcon = computed(() => (isRtl.value ? ArrowRight : ArrowLeft))
const templateId = computed(() => route.params.templateId as string)

function goBack(): void {
  router.push({ name: ROUTE_NAMES.ADMIN_DOCUMENTS })
}

// Points toward the referenced location, which flips with reading
// direction.
const jumpToIcon = computed(() => (isRtl.value ? CornerDownLeft : CornerDownRight))

const isLoading = ref(true)
const isSaving = ref(false)
const loadError = ref('')
const mergeFields = ref<MergeField[]>([])
const blocks = ref<TemplateBlock[]>([])
const searchQuery = ref('')

type RichInputInstance = InstanceType<typeof MergeFieldRichInput>

// Live handles to every rendered editor, keyed so `insertToken` can
// look one up and call its own imperative `insertToken` -- kept as
// plain (non-reactive) maps, since these hold DOM-backed component
// instances, not values Vue's reactivity has any business tracking.
const paragraphRefs = new Map<number, RichInputInstance>()
const cellRefs = new Map<string, RichInputInstance>()
function cellKey(blockIndex: number, rowIndex: number, cellIndex: number): string {
  return `${blockIndex}-${rowIndex}-${cellIndex}`
}
function setParagraphRef(blockIndex: number, el: RichInputInstance | null): void {
  if (el) paragraphRefs.set(blockIndex, el)
}
function setCellRef(blockIndex: number, rowIndex: number, cellIndex: number, el: RichInputInstance | null): void {
  if (el) cellRefs.set(cellKey(blockIndex, rowIndex, cellIndex), el)
}

// Which editor the next "insert field" click should target -- set by
// every paragraph/cell editor's own @focus handler.
type ActiveEditor =
  | { kind: 'paragraph'; blockIndex: number }
  | { kind: 'cell'; blockIndex: number; rowIndex: number; cellIndex: number }
const activeEditor = ref<ActiveEditor | null>(null)

function setActiveEditor(target: ActiveEditor): void {
  activeEditor.value = target
}

function loopVarFor(fieldKey: string | null | undefined): string | null {
  if (!fieldKey) return null
  return mergeFields.value.find((f) => f.key === fieldKey)?.loopVar ?? null
}

async function loadData(): Promise<void> {
  isLoading.value = true
  loadError.value = ''
  blocks.value = []
  searchQuery.value = ''
  activeEditor.value = null
  paragraphRefs.clear()
  cellRefs.clear()
  try {
    if (documentTemplateStore.templates.length === 0) await documentTemplateStore.loadTemplates()
    const template = documentTemplateStore.templates.find((item) => item.id === templateId.value)
    if (!template) return
    const [fields, layout] = await Promise.all([
      documentTemplateService.getMergeFields(template.documentType),
      documentTemplateService.getTemplateLayout(template.id),
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
}
onMounted(loadData)

const template = computed(() => documentTemplateStore.templates.find((item) => item.id === templateId.value))

function textFields(): MergeField[] {
  return mergeFields.value.filter((f) => f.kind === 'text')
}
function repeatingTableFields(): MergeField[] {
  return mergeFields.value.filter((f) => f.kind === 'repeating_table')
}
function repeatingListFields(): MergeField[] {
  return mergeFields.value.filter((f) => f.kind === 'repeating_list')
}

// --- Usage tracking: scans the whole document for where each field is
// currently placed, so the palette can show it instead of making the
// admin hunt through every paragraph/cell to find out. ---
interface Placement {
  label: string
  scrollTo: () => void
}

const blockLabels = computed<Map<number, string>>(() => {
  const labels = new Map<number, string>()
  let paragraphCount = 0
  let tableCount = 0
  for (const block of blocks.value) {
    if (block.kind === 'paragraph') {
      paragraphCount += 1
      labels.set(block.blockIndex, `Paragraph ${paragraphCount}`)
    } else {
      tableCount += 1
      labels.set(block.blockIndex, `Table ${tableCount}`)
    }
  }
  return labels
})

function scrollToBlock(blockIndex: number): void {
  nextTick(() => {
    document.getElementById(`mf-block-${blockIndex}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
}

/** How many times a plain text field's token appears anywhere in the
 * document (it can legitimately be placed more than once, e.g. a
 * client name in both a header and a footer paragraph). */
function textFieldUsageCount(field: MergeField): number {
  const token = `{{ ${field.key} }}`
  let count = 0
  for (const block of blocks.value) {
    if (block.kind === 'paragraph') {
      if ((block.text ?? '').includes(token)) count += 1
    } else {
      for (const row of block.rows ?? []) {
        for (const cell of row.cells) {
          if (cell.text.includes(token)) count += 1
        }
      }
    }
  }
  return count
}

/** Where a repeating-list field's single marker paragraph currently
 * is, if placed. */
function repeatingListPlacement(field: MergeField): Placement | undefined {
  const flagged = blocks.value.find((b) => b.kind === 'paragraph' && b.repeatingField === field.key)
  if (!flagged) return undefined
  return { label: blockLabels.value.get(flagged.blockIndex) ?? '', scrollTo: () => scrollToBlock(flagged.blockIndex) }
}

/** Where a repeating-table field's single marked row currently is, if
 * placed. */
function repeatingTablePlacement(field: MergeField): Placement | undefined {
  for (const block of blocks.value) {
    if (block.kind !== 'table') continue
    const row = block.rows?.find((r) => r.repeatingField === field.key)
    if (row) {
      return { label: blockLabels.value.get(block.blockIndex) ?? '', scrollTo: () => scrollToBlock(block.blockIndex) }
    }
  }
  return undefined
}

function fieldLabel(key: string): string {
  return mergeFields.value.find((f) => f.key === key)?.label ?? key
}

/** Unsets `fieldKey` from wherever it's currently flagged, and strips
 * its marker token(s) from that text too -- a repeating field can only
 * occupy one paragraph/row at a time, so marking a new location always
 * displaces the old one, and leaving the old token text behind would
 * leave a dangling `{{ loopVar }}`/`{{ loopVar.col }}` reference that
 * fails to render once it's no longer wrapped in a for/endfor. */
function clearRepeatingField(fieldKey: string): void {
  const field = mergeFields.value.find((f) => f.key === fieldKey)
  for (const block of blocks.value) {
    if (block.kind === 'paragraph' && block.repeatingField === fieldKey) {
      block.repeatingField = null
      if (field?.loopVar) block.text = stripToken(block.text ?? '', field.loopVar)
    } else if (block.kind === 'table') {
      for (const row of block.rows ?? []) {
        if (row.repeatingField === fieldKey) {
          row.repeatingField = null
          if (field?.loopVar) {
            for (const cell of row.cells) cell.text = stripColumnTokens(cell.text, field.loopVar)
          }
        }
      }
    }
  }
}

/** Removes every `{{ loopVar }}` occurrence (bare token) from `text`. */
function stripToken(text: string, loopVar: string): string {
  const re = new RegExp(`\\{\\{\\s*${loopVar}\\s*\\}\\}`, 'g')
  return text.replace(re, '').trim()
}

/** Removes every `{{ loopVar.column }}` occurrence (any column) from
 * `text`. */
function stripColumnTokens(text: string, loopVar: string): string {
  const re = new RegExp(`\\{\\{\\s*${loopVar}\\.[\\w]+\\s*\\}\\}`, 'g')
  return text.replace(re, '').trim()
}

function insertToken(token: string, markRepeatingField?: string): void {
  const target = activeEditor.value
  if (!target) {
    toastStore.show('info', t('administration.templateFieldMapperDialog.clickIntoDocumentFirstTitle'), t('administration.templateFieldMapperDialog.clickIntoDocumentFirstDescription'))
    return
  }
  const block = blocks.value.find((b) => b.blockIndex === target.blockIndex)
  if (!block) return

  if (target.kind === 'paragraph' && block.kind === 'paragraph') {
    const editor = paragraphRefs.get(target.blockIndex)
    if (!editor) return
    if (markRepeatingField) {
      clearRepeatingField(markRepeatingField)
      block.repeatingField = markRepeatingField
    }
    editor.insertToken(token)
  } else if (target.kind === 'cell' && block.kind === 'table') {
    const row = block.rows?.find((r) => r.rowIndex === target.rowIndex)
    if (!row) return
    const editor = cellRefs.get(cellKey(target.blockIndex, target.rowIndex, target.cellIndex))
    if (!editor) return
    if (markRepeatingField) {
      clearRepeatingField(markRepeatingField)
      row.repeatingField = markRepeatingField
    }
    editor.insertToken(token)
  }
}

function clearRowRepeating(row: TemplateRow, fieldKey: string | null | undefined): void {
  const loopVar = loopVarFor(fieldKey)
  row.repeatingField = null
  if (loopVar) for (const cell of row.cells) cell.text = stripColumnTokens(cell.text, loopVar)
}
function clearParagraphRepeating(block: TemplateBlock, fieldKey: string | null | undefined): void {
  const loopVar = loopVarFor(fieldKey)
  block.repeatingField = null
  if (loopVar) block.text = stripToken(block.text ?? '', loopVar)
}

/** A paragraph auto-fires this when its own marker chip is deleted
 * directly in the text -- the flag needs to follow. */
function handleParagraphRemoveRepeating(block: TemplateBlock): void {
  block.repeatingField = null
}

// --- Simple text filter -- dims non-matching blocks rather than
// hiding them, so a long document stays navigable (nothing seems to
// have vanished) while the admin can still spot the line they're
// after at a glance. ---
function blockMatchesSearch(block: TemplateBlock): boolean {
  const query = searchQuery.value.trim().toLowerCase()
  if (!query) return true
  if (block.kind === 'paragraph') return (block.text ?? '').toLowerCase().includes(query)
  return (block.rows ?? []).some((row) => row.cells.some((cell) => cell.text.toLowerCase().includes(query)))
}

async function handleSave(): Promise<void> {
  if (!template.value) return
  isSaving.value = true
  try {
    await documentTemplateService.saveTemplateMapping(template.value.id, blocks.value)
    toastStore.show('success', t('administration.templateFieldMapperDialog.fieldsMappedTitle'), t('administration.templateFieldMapperDialog.fieldsMappedDescription', { filename: template.value.originalFilename }))
    await documentTemplateStore.loadTemplates()
    goBack()
  } catch (error) {
    toastStore.show('error', t('administration.templateFieldMapperDialog.couldNotSaveMapping'), error instanceof Error ? error.message : t('common.pleaseTryAgain'))
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div class="flex flex-col gap-6 p-6">
    <BaseButton variant="ghost" size="sm" :icon="backIcon" class="self-start no-print" :disabled="isSaving" @click="goBack">
      {{ t('administration.documentTemplates.backToDocuments') }}
    </BaseButton>

    <div v-if="isLoading" class="rounded-xl border border-border-light bg-bg-card p-5">
      <SkeletonLoader :rows="6" />
    </div>

    <EmptyState
      v-else-if="!template"
      :title="t('administration.documentTemplates.templateNotFoundTitle')"
      :description="t('administration.documentTemplates.templateNotFoundDescription')"
    />

    <div v-else class="flex flex-col gap-5 rounded-xl border border-border-light bg-bg-card p-5">
      <h1 class="text-lg font-semibold text-text-primary">
        {{ t('administration.templateFieldMapperDialog.mapFieldsTitle', { filename: template.originalFilename }) }}
      </h1>

      <p v-if="loadError" class="text-sm text-danger-600">{{ loadError }}</p>

      <template v-else>
        <p class="text-xs text-text-muted">
          {{ t('administration.templateFieldMapperDialog.intro') }}
        </p>

        <!-- Field palette -->
        <div class="flex flex-col gap-3 rounded-lg border border-border-light bg-bg-secondary p-3">
          <div class="flex flex-wrap gap-2">
            <button
              v-for="field in textFields()"
              :key="field.key"
              type="button"
              class="inline-flex items-center gap-1.5 rounded-full border border-border-default bg-bg-card px-3 py-1 text-xs font-medium text-text-secondary transition-colors duration-fast hover:border-accent-500 hover:text-accent-600"
              @click="insertToken(`{{ ${field.key} }}`)"
            >
              {{ field.label }}
              <span v-if="textFieldUsageCount(field) > 0" class="rounded-full bg-accent-100 px-1.5 py-0.5 text-[10px] text-accent-700">
                ×{{ textFieldUsageCount(field) }}
              </span>
            </button>
          </div>

          <div v-for="field in repeatingTableFields()" :key="field.key" class="flex flex-col gap-1.5 border-t border-border-light pt-3">
            <div class="flex flex-wrap items-center gap-2 text-xs text-text-muted">
              <Repeat class="h-3.5 w-3.5" />
              <span>{{ t('administration.templateFieldMapperDialog.tableColumnsHint', { label: field.label }) }}</span>
              <button
                v-if="repeatingTablePlacement(field)"
                type="button"
                class="inline-flex items-center gap-1 text-accent-600 hover:text-accent-700"
                @click="repeatingTablePlacement(field)?.scrollTo()"
              >
                <component :is="jumpToIcon" class="h-3 w-3" />
                {{ t('administration.templateFieldMapperDialog.repeatingAt', { label: repeatingTablePlacement(field)?.label }) }}
              </button>
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="column in field.columns"
                :key="column.key"
                type="button"
                :disabled="activeEditor?.kind !== 'cell'"
                class="rounded-full border border-border-default bg-bg-card px-3 py-1 text-xs font-medium text-text-secondary transition-colors duration-fast hover:border-accent-500 hover:text-accent-600 disabled:cursor-not-allowed disabled:opacity-40"
                @click="insertToken(`{{ ${field.loopVar}.${column.key} }}`, field.key)"
              >
                {{ column.label }}
              </button>
            </div>
          </div>

          <div v-for="field in repeatingListFields()" :key="field.key" class="flex flex-col gap-1.5 border-t border-border-light pt-3">
            <div class="flex flex-wrap items-center gap-2 text-xs text-text-muted">
              <Repeat class="h-3.5 w-3.5" />
              <span>{{ t('administration.templateFieldMapperDialog.listFieldHint', { label: field.label }) }}</span>
              <button
                v-if="repeatingListPlacement(field)"
                type="button"
                class="inline-flex items-center gap-1 text-accent-600 hover:text-accent-700"
                @click="repeatingListPlacement(field)?.scrollTo()"
              >
                <component :is="jumpToIcon" class="h-3 w-3" />
                {{ t('administration.templateFieldMapperDialog.repeatingAt', { label: repeatingListPlacement(field)?.label }) }}
              </button>
            </div>
            <button
              type="button"
              :disabled="activeEditor?.kind !== 'paragraph'"
              class="w-fit rounded-full border border-border-default bg-bg-card px-3 py-1 text-xs font-medium text-text-secondary transition-colors duration-fast hover:border-accent-500 hover:text-accent-600 disabled:cursor-not-allowed disabled:opacity-40"
              @click="insertToken(`{{ ${field.loopVar} }}`, field.key)"
            >
              {{ field.label }}
            </button>
          </div>
        </div>

        <SearchBox v-model="searchQuery" :placeholder="t('administration.templateFieldMapperDialog.searchPlaceholder')" :debounce-ms="0" />

        <!-- Document body -->
        <div class="flex max-h-[55vh] flex-col gap-3 overflow-y-auto rounded-lg border border-border-light p-3">
          <template v-for="block in blocks" :key="`${block.kind}-${block.blockIndex}`">
            <div
              v-if="block.kind === 'paragraph'"
              :id="`mf-block-${block.blockIndex}`"
              class="flex flex-col gap-1 transition-opacity duration-fast"
              :class="{ 'opacity-30': !blockMatchesSearch(block) }"
            >
              <MergeFieldRichInput
                :model-value="block.text ?? ''"
                @update:model-value="block.text = $event"
                :fields="mergeFields"
                :repeating-loop-var="loopVarFor(block.repeatingField)"
                :placeholder="t('administration.templateFieldMapperDialog.emptyLine')"
                :ref="(el) => setParagraphRef(block.blockIndex, el as RichInputInstance | null)"
                @focus="setActiveEditor({ kind: 'paragraph', blockIndex: block.blockIndex })"
                @remove-repeating="handleParagraphRemoveRepeating(block)"
              />
              <div v-if="block.repeatingField" class="flex items-center gap-1 text-[11px] text-accent-600">
                <Repeat class="h-3 w-3" />
                <span>{{ t('administration.templateFieldMapperDialog.repeatsForEach', { label: fieldLabel(block.repeatingField) }) }}</span>
                <button
                  type="button"
                  class="hover:text-accent-700"
                  :aria-label="t('administration.templateFieldMapperDialog.clearRepeatingField')"
                  @click="clearParagraphRepeating(block, block.repeatingField)"
                >
                  <X class="h-3 w-3" />
                </button>
              </div>
            </div>

            <div v-if="block.kind === 'table'" :id="`mf-block-${block.blockIndex}`" class="overflow-x-auto transition-opacity duration-fast" :class="{ 'opacity-30': !blockMatchesSearch(block) }">
              <table class="w-full border-collapse text-sm">
                <tbody>
                  <tr v-for="row in block.rows" :key="row.rowIndex">
                    <td v-for="cell in row.cells" :key="cell.cellIndex" class="border border-border-light p-1 align-top">
                      <MergeFieldRichInput
                        v-model="cell.text"
                        :fields="mergeFields"
                        :repeating-loop-var="loopVarFor(row.repeatingField)"
                        class="min-w-[10rem]"
                        :ref="(el) => setCellRef(block.blockIndex, row.rowIndex, cell.cellIndex, el as RichInputInstance | null)"
                        @focus="
                          setActiveEditor({
                            kind: 'cell',
                            blockIndex: block.blockIndex,
                            rowIndex: row.rowIndex,
                            cellIndex: cell.cellIndex,
                          })
                        "
                      />
                    </td>
                    <td v-if="row.repeatingField" class="whitespace-nowrap p-1 align-top text-[11px] text-accent-600">
                      <span class="inline-flex items-center gap-1">
                        <Repeat class="h-3 w-3" />
                        {{ t('administration.templateFieldMapperDialog.repeats', { label: fieldLabel(row.repeatingField) }) }}
                        <button
                          type="button"
                          class="hover:text-accent-700"
                          :aria-label="t('administration.templateFieldMapperDialog.clearRepeatingField')"
                          @click="clearRowRepeating(row, row.repeatingField)"
                        >
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

        <FormActionBar :submit-label="t('administration.templateFieldMapperDialog.saveMapping')" :loading="isSaving" @submit="handleSave" @cancel="goBack" />
      </template>
    </div>
  </div>
</template>
