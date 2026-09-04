<script setup lang="ts">
import AmbientBackground from '@/components/common/AmbientBackground.vue'
</script>

<template>
  <div
    class="flex min-h-screen items-center justify-center px-4 py-12"
  >
    <AmbientBackground />
    <div class="w-full max-w-md">
      <div class="mb-8 flex items-center justify-center gap-2">
        <div
          class="gradient-luxe flex h-10 w-10 items-center justify-center rounded-lg text-sm font-semibold text-white shadow-glass-sm"
        >
          SO
        </div>
        <span class="text-lg font-semibold text-[var(--color-text-primary)]">ServiceOS</span>
      </div>

      <div
        id="main-content"
        tabindex="-1"
        class="glass-panel rounded-xl p-8 shadow-glass outline-none"
      >
        <RouterView v-slot="{ Component }">
          <Transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </Transition>
        </RouterView>
      </div>

      <p class="mt-6 text-center text-xs text-[var(--color-text-muted)]">
        &copy; {{ new Date().getFullYear() }} Almailam Engineering Consultants
      </p>
    </div>
  </div>
</template>
