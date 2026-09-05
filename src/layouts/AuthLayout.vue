<script setup lang="ts">
import { Compass } from '@lucide/vue'
import AmbientBackground from '@/components/common/AmbientBackground.vue'
</script>

<template>
  <div class="relative flex min-h-screen flex-col laptop:flex-row">
    <AmbientBackground />

    <!-- Brand panel: mirrors the split-screen richness of the app's other
         login screens (big serif headline, tagline, badge row) but in
         Almailam's own jade/graphite palette rather than reusing gold, so
         the two apps read as distinct products, not the same theme
         reskinned. Hidden below the laptop breakpoint -- the sign-in
         card's own compact wordmark (below) carries the branding on a
         single mobile column instead. -->
    <div class="relative z-10 hidden flex-1 flex-col justify-between px-16 py-16 laptop:flex">
      <div class="flex items-center gap-3">
        <div
          class="gradient-luxe-accent flex h-10 w-10 items-center justify-center rounded-lg shadow-glass-sm"
        >
          <Compass class="h-5 w-5 text-white" :stroke-width="1.75" />
        </div>
        <span class="text-lg font-semibold tracking-wide text-[var(--color-text-primary)]">ServiceOS</span>
      </div>

      <div>
        <h1 class="font-display text-5xl leading-[1.15] text-[var(--color-text-primary)]">
          Precision in <span class="text-gradient-accent">every project.</span>
        </h1>
        <p class="mt-6 max-w-md text-base text-[var(--color-text-secondary)]">
          Projects, clients, quotations, contracts, and government submissions
          in one connected workspace -- built for the engineering consultants
          who deliver with confidence.
        </p>
      </div>

      <div
        class="flex items-center gap-3 text-xs font-medium uppercase tracking-widest text-[var(--color-text-muted)]"
      >
        <span>Trusted workflows</span>
        <span class="h-1 w-1 rounded-full bg-accent-500" />
        <span>Real-time insights</span>
      </div>
    </div>

    <!-- Sign-in panel -->
    <div class="relative z-10 flex flex-1 items-center justify-center px-4 py-12 laptop:px-16">
      <div class="w-full max-w-md">
        <div class="mb-8 flex items-center justify-center gap-2 laptop:hidden">
          <div
            class="gradient-luxe-accent flex h-10 w-10 items-center justify-center rounded-lg shadow-glass-sm"
          >
            <Compass class="h-5 w-5 text-white" :stroke-width="1.75" />
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
  </div>
</template>
