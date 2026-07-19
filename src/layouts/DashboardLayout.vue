<script setup lang="ts">
import Breadcrumb from '@/components/navigation/Breadcrumb.vue'
import MobileSidebar from '@/components/navigation/MobileSidebar.vue'
import Sidebar from '@/components/navigation/Sidebar.vue'
import TopNavigation from '@/components/navigation/TopNavigation.vue'
import PageFooter from '@/components/common/PageFooter.vue'
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-[var(--color-bg-page)]">
    <Sidebar />
    <MobileSidebar />

    <div class="flex min-w-0 flex-1 flex-col">
      <TopNavigation />
      <Breadcrumb />

      <main class="flex-1 overflow-y-auto">
        <RouterView />
      </main>

      <PageFooter />
    </div>
  </div>
</template>
