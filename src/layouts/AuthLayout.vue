<script setup lang="ts"></script>

<template>
  <div
    class="flex min-h-screen items-center justify-center bg-[var(--color-bg-page)] px-4 py-12"
  >
    <div class="w-full max-w-md">
      <div class="mb-8 flex items-center justify-center gap-2">
        <div
          class="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-600 text-sm font-semibold text-white"
        >
          SO
        </div>
        <span class="text-lg font-semibold text-[var(--color-text-primary)]">ServiceOS</span>
      </div>

      <div
        class="rounded-xl border border-[var(--color-border-default)] bg-[var(--color-bg-card)] p-8 shadow-soft"
      >
        <RouterView />
      </div>

      <p class="mt-6 text-center text-xs text-[var(--color-text-muted)]">
        &copy; {{ new Date().getFullYear() }} Almailam Engineering Consultants
      </p>
    </div>
  </div>
</template>
