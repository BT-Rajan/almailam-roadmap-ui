<script setup lang="ts">
import { CloudUpload, FileText, X } from '@lucide/vue'
import { ref, useId } from 'vue'

interface Props {
  accept?: string
  hint?: string
  // Both optional and undefined by default, so every other use of this
  // component (project documents, client documents, new versions) keeps
  // its current no-restriction behaviour. Only a caller that explicitly
  // sets these (the New Client wizard's identification upload) gets
  // client-side enforcement.
  maxSizeBytes?: number
  allowedExtensions?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  accept: '.pdf,.doc,.docx,.dwg,.xlsx,.png,.jpg',
  hint: 'PDF, Word, Excel, DWG or image files',
  maxSizeBytes: undefined,
  allowedExtensions: undefined,
})

const emit = defineEmits<{
  select: [file: File | undefined]
  // Fired instead of `select` when maxSizeBytes/allowedExtensions are
  // set and the chosen file fails either check -- the file is never
  // accepted into selectedFile in that case.
  error: [message: string]
}>()

const inputId = useId()
const isDragging = ref(false)
const selectedFile = ref<File>()

function validationError(file: File): string | undefined {
  if (props.allowedExtensions) {
    const extension = `.${file.name.split('.').pop()?.toLowerCase() ?? ''}`
    if (!props.allowedExtensions.includes(extension)) {
      return `File type '${extension}' is not allowed. Allowed types: ${props.allowedExtensions.join(', ')}`
    }
  }
  if (props.maxSizeBytes !== undefined && file.size > props.maxSizeBytes) {
    const maxMb = (props.maxSizeBytes / (1024 * 1024)).toFixed(0)
    return `File exceeds the ${maxMb} MB upload limit.`
  }
  return undefined
}

function selectFile(file: File | undefined): void {
  if (file) {
    const error = validationError(file)
    if (error) {
      emit('error', error)
      return
    }
  }
  selectedFile.value = file
  emit('select', file)
}

function handleDrop(event: DragEvent): void {
  isDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  selectFile(file)
}

function handleInputChange(event: Event): void {
  const file = (event.target as HTMLInputElement).files?.[0]
  selectFile(file)
}

function clearFile(): void {
  selectFile(undefined)
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <label
      v-if="!selectedFile"
      :for="inputId"
      class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-6 py-8 text-center transition-colors duration-fast"
      :class="isDragging ? 'border-primary-500 bg-primary-50' : 'border-border-default bg-bg-secondary hover:border-primary-400'"
      @dragover.prevent="isDragging = true"
      @dragleave.prevent="isDragging = false"
      @drop.prevent="handleDrop"
    >
      <CloudUpload class="h-8 w-8 text-text-muted" />
      <p class="text-sm font-medium text-text-secondary">Click to upload or drag and drop</p>
      <p class="text-xs text-text-muted">{{ hint }}</p>
      <input :id="inputId" type="file" :accept="accept" class="hidden" @change="handleInputChange" />
    </label>

    <div v-else class="flex items-center gap-3 rounded-lg border border-border-light bg-bg-card px-4 py-3">
      <FileText class="h-5 w-5 shrink-0 text-primary-600" />
      <span class="flex-1 truncate text-sm font-medium text-text-secondary">{{ selectedFile.name }}</span>
      <button
        type="button"
        aria-label="Remove file"
        class="text-text-muted hover:text-text-secondary"
        @click="clearFile"
      >
        <X class="h-4 w-4" />
      </button>
    </div>
  </div>
</template>
