<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { clientService } from '@/services/clientService'
import { projectService } from '@/services/projectService'

// Type-to-search picker for reports: the browser's own <datalist> filters
// every live project (or client) by number and name as you type, keyboard
// included, with no full records downloaded. `clearable` pickers treat an
// emptied box as "all".
const props = withDefaults(defineProps<{ modelValue: string | undefined; kind?: 'project' | 'client'; clearable?: boolean }>(), {
  kind: 'project',
  clearable: false,
})
const emit = defineEmits<{ 'update:modelValue': [id: string] }>()
const { t } = useI18n()

const options = ref<{ id: string; name: string }[]>([])
const text = ref('')
const loadFailed = ref(false)
const listId = `report-${props.kind}s-${Math.random().toString(36).slice(2, 8)}`

const labelFor = (option: { id: string; name: string }) => (props.kind === 'project' ? `${option.id} · ${option.name}` : option.name)
const byLabel = computed(() => new Map(options.value.map((option) => [labelFor(option), option.id])))
const keys = computed(() => (props.kind === 'project' ? 'projectPicker' : 'clientPicker'))

function syncText(): void {
  const current = options.value.find((option) => option.id === props.modelValue)
  text.value = current ? labelFor(current) : ''
}

onMounted(async () => {
  try {
    options.value = props.kind === 'project' ? await projectService.getProjectOptions() : await clientService.getClientOptions()
  } catch {
    loadFailed.value = true
  }
  syncText()
})
watch(() => props.modelValue, syncText)

function onChange(): void {
  const typed = text.value.trim()
  if (!typed && props.clearable) {
    if (props.modelValue) emit('update:modelValue', '')
    return
  }
  // An exact label from the list, or a bare id/number.
  const id = byLabel.value.get(typed) ?? options.value.find((option) => option.id === typed)?.id
  if (id && id !== props.modelValue) emit('update:modelValue', id)
  else if (!id) syncText()
}
</script>

<template>
  <div class="flex w-full max-w-sm flex-col gap-1.5 print:hidden">
    <label :for="`${listId}-input`" class="text-sm font-medium text-text-secondary">{{ t(`report.${keys}.label`) }}</label>
    <input
      :id="`${listId}-input`"
      v-model="text"
      type="search"
      :list="listId"
      autocomplete="off"
      :placeholder="clearable ? t(`report.${keys}.placeholderAll`) : t(`report.${keys}.placeholder`)"
      class="h-10 rounded-lg border border-border-default bg-bg-card px-3 text-sm text-text-primary outline-none focus:border-accent-500 focus:ring-2 focus:ring-accent-500/20"
      @change="onChange"
      @search="onChange"
      @focus="($event.target as HTMLInputElement).select()"
    />
    <datalist :id="listId">
      <option v-for="option in options" :key="option.id" :value="labelFor(option)" />
    </datalist>
    <p v-if="loadFailed" class="text-xs text-danger-600">{{ t(`report.${keys}.loadFailed`) }}</p>
  </div>
</template>
