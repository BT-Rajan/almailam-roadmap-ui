<script setup lang="ts">
import { Download, Printer } from '@lucide/vue'
import { computed, reactive, ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import TextInput from '@/components/common/TextInput.vue'
import { governmentFormService } from '@/services/governmentFormService'
import type { GovernmentForm } from '@/types/Government'
import { triggerBlobDownload } from '@/utils/fileDownload'
import { extractTemplateTokens, renderGovernmentFormTemplate } from '@/utils/governmentFormHelpers'

interface Props {
  modelValue: boolean
  form?: GovernmentForm
  // Starting values for each token -- sample data when previewing from
  // the admin screen (no real project behind this view), overridable by
  // hand in the fields below. Any token left blank renders as a blank
  // line -- see renderGovernmentFormTemplate.
  context?: Record<string, string | undefined>
  // Shown above the fields when the caller wants to make clear this
  // isn't tied to a real project -- see AdminFormsPage.vue.
  stubNotice?: string
}

const props = withDefaults(defineProps<Props>(), {
  form: undefined,
  context: () => ({}),
  stubNotice: undefined,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const tokens = computed(() => (props.form?.template ? extractTemplateTokens(props.form.template) : []))
const contextValues = reactive<Record<string, string>>({})
const isDownloading = ref(false)
const downloadError = ref('')

function humanizeToken(token: string): string {
  const spaced = token.replace(/([a-z])([A-Z])/g, '$1 $2')
  return spaced.charAt(0).toUpperCase() + spaced.slice(1)
}

// Re-seeds from the sample/starting context every time a different form
// is opened for preview -- edits made to one form's fields shouldn't
// leak into the next form's fields if the dialog is reused.
watch(
  () => props.form,
  (form) => {
    for (const key of Object.keys(contextValues)) delete contextValues[key]
    if (!form?.template) return
    for (const token of extractTemplateTokens(form.template)) {
      contextValues[token] = props.context[token] ?? ''
    }
    downloadError.value = ''
  },
  { immediate: true },
)

const renderedBody = computed(() => {
  if (!props.form?.template) return ''
  return renderGovernmentFormTemplate(props.form.template, contextValues)
})

function printPreview(): void {
  const printWindow = window.open('', '_blank')
  if (!printWindow || !props.form) return
  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>${props.form.formCode} – ${props.form.title}</title>
        <style>
          body { font-family: -apple-system, sans-serif; padding: 40px; color: #1a1a2e; white-space: pre-wrap; line-height: 1.6; }
          h1 { font-size: 18px; margin-bottom: 24px; }
        </style>
      </head>
      <body>
        <h1>${props.form.title}</h1>
        ${renderedBody.value.replace(/\n/g, '<br/>')}
      </body>
    </html>
  `)
  printWindow.document.close()
  printWindow.focus()
  printWindow.print()
}

async function downloadPdf(): Promise<void> {
  if (!props.form) return
  downloadError.value = ''
  isDownloading.value = true
  try {
    const blob = await governmentFormService.renderPdf(props.form.id, {
      context: { ...contextValues },
      title: props.form.title,
    })
    triggerBlobDownload(blob, `${props.form.formCode}.pdf`)
  } catch (error) {
    downloadError.value = error instanceof Error ? error.message : 'Failed to generate PDF'
  } finally {
    isDownloading.value = false
  }
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="form ? `Preview · ${form.title}` : 'Preview'"
    size="lg"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div v-if="form" class="flex flex-col gap-4">
      <p v-if="stubNotice" class="rounded-lg border border-warning-200 bg-warning-50 px-3 py-2 text-xs text-warning-800">
        {{ stubNotice }}
      </p>

      <EmptyState
        v-if="!form.template"
        title="No template yet"
        description="Add template content to this form to preview it filled in."
      />

      <template v-else>
        <div v-if="tokens.length > 0" class="flex flex-col gap-3">
          <p class="text-xs font-medium uppercase tracking-wide text-text-muted">Fill in the details</p>
          <div class="grid grid-cols-1 gap-3 tablet:grid-cols-2">
            <TextInput
              v-for="token in tokens"
              :key="token"
              v-model="contextValues[token]"
              :label="humanizeToken(token)"
            />
          </div>
        </div>

        <div>
          <p class="mb-1.5 text-xs font-medium uppercase tracking-wide text-text-muted">Preview</p>
          <pre
            class="max-h-72 overflow-y-auto whitespace-pre-wrap rounded-lg border border-border-light bg-bg-card p-5 font-sans text-sm leading-relaxed text-text-primary"
            >{{ renderedBody }}</pre
          >
        </div>

        <p v-if="downloadError" class="text-xs text-danger-600">{{ downloadError }}</p>
      </template>
    </div>

    <template v-if="form" #footer>
      <BaseButton variant="secondary" :icon="Printer" :disabled="!form.template" @click="printPreview">Print</BaseButton>
      <BaseButton :icon="Download" :disabled="!form.template" :loading="isDownloading" @click="downloadPdf">
        Save as PDF
      </BaseButton>
    </template>
  </BaseDialog>
</template>
