<script setup lang="ts">
import { CloudUpload, FileText, X } from '@lucide/vue'
import { ref, useId } from 'vue'

interface Props {
  accept?: string
  hint?: string
}

withDefaults(defineProps<Props>(), {
  accept: '.pdf,.doc,.docx,.dwg,.xlsx,.png,.jpg',
  hint: 'PDF, Word, Excel, DWG or image files',
})

const emit = defineEmits<{
  select: [file: File | undefined]
}>()

const inputId = useId()
const isDragging = ref(false)
const selectedFile = ref<File>()

function selectFile(file: File | undefined): void {
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
      <CloudUpload class="h-8 w-8 text-neutral-400" />
      <p class="text-sm font-medium text-neutral-700">Click to upload or drag and drop</p>
      <p class="text-xs text-neutral-400">{{ hint }}</p>
      <input :id="inputId" type="file" :accept="accept" class="hidden" @change="handleInputChange" />
    </label>

    <div v-else class="flex items-center gap-3 rounded-lg border border-border-light bg-bg-card px-4 py-3">
      <FileText class="h-5 w-5 shrink-0 text-primary-600" />
      <span class="flex-1 truncate text-sm font-medium text-neutral-700">{{ selectedFile.name }}</span>
      <button
        type="button"
        aria-label="Remove file"
        class="text-neutral-400 hover:text-neutral-600"
        @click="clearFile"
      >
        <X class="h-4 w-4" />
      </button>
    </div>
  </div>
</template>
