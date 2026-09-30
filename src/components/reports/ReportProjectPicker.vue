<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { projectService } from '@/services/projectService'

// Type-to-search project picker for reports: the browser's own <datalist>
// filters every live project (number + name) as you type, keyboard
// included, with no full project records downloaded.
const props = defineProps<{ modelValue: string | undefined }>()
const emit = defineEmits<{ 'update:modelValue': [projectNo: string] }>()
const { t } = useI18n()

const options = ref<{ id: string; name: string }[]>([])
const text = ref('')
const loadFailed = ref(false)
const listId = `report-projects-${Math.random().toString(36).slice(2, 8)}`

const labelFor = (option: { id: string; name: string }) => `${option.id} · ${option.name}`
const byLabel = computed(() => new Map(options.value.map((option) => [labelFor(option), option.id])))

function syncText(): void {
  const current = options.value.find((option) => option.id === props.modelValue)
  text.value = current ? labelFor(current) : ''
}

onMounted(async () => {
  try {
    options.value = await projectService.getProjectOptions()
  } catch {
    loadFailed.value = true
  }
  syncText()
})
watch(() => props.modelValue, syncText)

function onChange(): void {
  const typed = text.value.trim()
  // An exact label from the list, or a bare project number.
  const projectNo = byLabel.value.get(typed) ?? options.value.find((option) => option.id === typed)?.id
  if (projectNo && projectNo !== props.modelValue) emit('update:modelValue', projectNo)
  else if (!projectNo) syncText()
}
</script>

<template>
  <div class="flex w-full max-w-md flex-col gap-1.5 print:hidden">
    <label :for="`${listId}-input`" class="text-sm font-medium text-text-secondary">{{ t('report.projectPicker.label') }}</label>
    <input
      :id="`${listId}-input`"
      v-model="text"
      type="text"
      :list="listId"
      autocomplete="off"
      :placeholder="t('report.projectPicker.placeholder')"
      class="h-10 rounded-lg border border-border-default bg-bg-card px-3 text-sm text-text-primary outline-none focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
      @change="onChange"
      @focus="($event.target as HTMLInputElement).select()"
    />
    <datalist :id="listId">
      <option v-for="option in options" :key="option.id" :value="labelFor(option)" />
    </datalist>
    <p v-if="loadFailed" class="text-xs text-danger-600">{{ t('report.projectPicker.loadFailed') }}</p>
  </div>
</template>
