<script setup lang="ts">
import { ChevronLeft, ChevronRight, FileText, ZoomIn, ZoomOut } from '@lucide/vue'
import { computed, ref } from 'vue'

import IconButton from '@/components/common/IconButton.vue'

interface Props {
  title: string
  pageCount?: number
}

const props = withDefaults(defineProps<Props>(), {
  pageCount: 4,
})

const currentPage = ref(1)
const zoomLevel = ref(100)

const canGoPrevious = computed(() => currentPage.value > 1)
const canGoNext = computed(() => currentPage.value < props.pageCount)

function goToPreviousPage(): void {
  if (canGoPrevious.value) currentPage.value -= 1
}

function goToNextPage(): void {
  if (canGoNext.value) currentPage.value += 1
}

function zoomOut(): void {
  zoomLevel.value = Math.max(50, zoomLevel.value - 25)
}

function zoomIn(): void {
  zoomLevel.value = Math.min(200, zoomLevel.value + 25)
}
</script>

<template>
  <div class="flex flex-col gap-3">
    <div class="flex items-center justify-between rounded-lg border border-border-light bg-bg-secondary px-3 py-2">
      <div class="flex items-center gap-1">
        <IconButton :icon="ChevronLeft" label="Previous page" size="sm" :disabled="!canGoPrevious" @click="goToPreviousPage" />
        <span class="px-2 text-sm text-neutral-600">Page {{ currentPage }} of {{ pageCount }}</span>
        <IconButton :icon="ChevronRight" label="Next page" size="sm" :disabled="!canGoNext" @click="goToNextPage" />
      </div>
      <div class="flex items-center gap-1">
        <IconButton :icon="ZoomOut" label="Zoom out" size="sm" :disabled="zoomLevel <= 50" @click="zoomOut" />
        <span class="w-12 text-center text-sm text-neutral-600">{{ zoomLevel }}%</span>
        <IconButton :icon="ZoomIn" label="Zoom in" size="sm" :disabled="zoomLevel >= 200" @click="zoomIn" />
      </div>
    </div>

    <div class="flex min-h-[420px] items-center justify-center overflow-auto rounded-lg border border-border-light bg-neutral-100 p-6">
      <div
        class="flex aspect-[3/4] w-full max-w-md flex-col items-center justify-center gap-3 rounded-md bg-bg-card p-8 text-center shadow-medium transition-all duration-normal"
        :style="{ transform: `scale(${zoomLevel / 100})` }"
      >
        <FileText class="h-12 w-12 text-neutral-300" />
        <p class="text-sm font-medium text-neutral-600">{{ title }}</p>
        <p class="text-xs text-neutral-400">Preview page {{ currentPage }}</p>
      </div>
    </div>
  </div>
</template>
