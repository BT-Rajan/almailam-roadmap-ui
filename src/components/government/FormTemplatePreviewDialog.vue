<script setup lang="ts">
import { Printer } from '@lucide/vue'
import { computed } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { GovernmentForm } from '@/types/Government'
import { renderGovernmentFormTemplate } from '@/utils/governmentFormHelpers'

interface Props {
  modelValue: boolean
  form?: GovernmentForm
  // Merge values known for the current context (a project/client, or just
  // sample data when previewing from the admin screen). Any token not
  // present here renders as a blank line -- see renderGovernmentFormTemplate.
  context?: Record<string, string | undefined>
  // Shown above the rendered body when the caller wants to make clear this
  // isn't yet a real, DB-generated document.
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

const renderedBody = computed(() => {
  if (!props.form?.template) return ''
  return renderGovernmentFormTemplate(props.form.template, props.context)
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
      <pre
        v-else
        class="whitespace-pre-wrap rounded-lg border border-border-light bg-bg-card p-5 font-sans text-sm leading-relaxed text-text-primary"
        >{{ renderedBody }}</pre
      >
    </div>

    <template v-if="form" #footer>
      <BaseButton variant="secondary" :icon="Printer" :disabled="!form.template" @click="printPreview">Print</BaseButton>
    </template>
  </BaseDialog>
</template>
