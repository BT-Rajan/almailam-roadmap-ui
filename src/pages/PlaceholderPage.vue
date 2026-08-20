<script setup lang="ts">
defineProps<{
  title?: string
}>()
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-bg-secondary px-6">
    <div class="text-center">
      <p class="text-sm font-medium uppercase tracking-wide text-primary-600">ServiceOS</p>
      <h1 class="mt-2 text-2xl font-semibold text-text-primary">{{ title ?? 'Coming Soon' }}</h1>
      <p class="mt-2 text-sm text-text-muted">
        This screen will be implemented in an upcoming development pass.
      </p>
    </div>
  </div>
</template>
