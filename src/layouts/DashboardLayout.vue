<script setup lang="ts">
import Breadcrumb from '@/components/navigation/Breadcrumb.vue'
import MobileSidebar from '@/components/navigation/MobileSidebar.vue'
import Sidebar from '@/components/navigation/Sidebar.vue'
import TopNavigation from '@/components/navigation/TopNavigation.vue'
import PageFooter from '@/components/common/PageFooter.vue'
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-[var(--color-bg-page)] print:h-auto print:overflow-visible">
    <Sidebar class="no-print" />
    <MobileSidebar class="no-print" />

    <div class="flex min-w-0 flex-1 flex-col print:overflow-visible">
      <TopNavigation class="no-print" />
      <Breadcrumb class="no-print" />

      <main class="flex-1 overflow-y-auto print:overflow-visible">
        <RouterView />
      </main>

      <PageFooter class="no-print" />
    </div>
  </div>
</template>
