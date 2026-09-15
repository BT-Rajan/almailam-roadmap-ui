<script setup lang="ts">
import { Camera } from '@lucide/vue'
import { onUnmounted, reactive, watch } from 'vue'

import { sitePortalService } from '@/services/sitePortalService'
import { openBlobInWindow } from '@/utils/fileDownload'
import type { StatusReportImage } from '@/types/StatusReport'

// Read-only viewer for a report's already-saved photos -- used on the
// review side (StatusReportInboxPage.vue, TaskFieldReportHistory.vue),
// unlike SitePortalReportPage.vue's own inline picker which also needs
// upload/remove and so keeps that logic local to itself rather than
// sharing this component.
const props = defineProps<{
  reportId: string
  images: StatusReportImage[]
}>()

// Served through an authenticated endpoint like every other uploaded
// file in this app, not a public/static URL -- fetched on demand rather
// than trusted as a plain src, same reasoning as the site-portal
// picker's own thumbnail loading.
const thumbnailUrls = reactive<Record<string, string>>({})

async function loadThumbnail(image: StatusReportImage): Promise<void> {
  if (thumbnailUrls[image.id]) return
  try {
    const blob = await sitePortalService.getReportImageBlob(props.reportId, image.id)
    thumbnailUrls[image.id] = URL.createObjectURL(blob)
  } catch {
    // Leave it without a thumbnail -- clicking still retries the fetch
    // fresh via viewImage below.
  }
}

watch(
  () => props.images,
  (images) => {
    for (const image of images) void loadThumbnail(image)
  },
  { immediate: true },
)

onUnmounted(() => {
  for (const url of Object.values(thumbnailUrls)) URL.revokeObjectURL(url)
})

async function viewImage(image: StatusReportImage): Promise<void> {
  const printWindow = window.open('', '_blank')
  try {
    const blob = thumbnailUrls[image.id]
      ? await fetch(thumbnailUrls[image.id]).then((r) => r.blob())
      : await sitePortalService.getReportImageBlob(props.reportId, image.id)
    openBlobInWindow(blob, printWindow)
  } catch {
    printWindow?.close()
  }
}
</script>

<template>
  <div v-if="images.length > 0" class="flex flex-wrap gap-2">
    <button
      v-for="image in images"
      :key="image.id"
      type="button"
      class="h-16 w-16 shrink-0 overflow-hidden rounded-lg border border-border-light bg-bg-secondary"
      :title="image.filename"
      @click="viewImage(image)"
    >
      <img v-if="thumbnailUrls[image.id]" :src="thumbnailUrls[image.id]" :alt="image.filename" class="h-full w-full object-cover" />
      <span v-else class="flex h-full w-full items-center justify-center">
        <Camera class="h-5 w-5 text-text-muted" />
      </span>
    </button>
  </div>
</template>
