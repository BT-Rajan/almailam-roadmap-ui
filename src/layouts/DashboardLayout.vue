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

      <main id="main-content" tabindex="-1" class="flex-1 overflow-y-auto outline-none print:overflow-visible">
        <RouterView v-slot="{ Component }">
          <Transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </main>

      <PageFooter class="no-print" />
    </div>
  </div>
</template>
