<script setup lang="ts">
const currentYear = new Date().getFullYear()
</script>

<template>
  <footer
    class="flex h-14 shrink-0 items-center justify-between border-t border-[var(--color-border-default)] px-4 text-xs text-[var(--color-text-muted)] lg:px-6"
  >
    <span>&copy; {{ currentYear }} Almailam Engineering Consultants</span>
    <span>ServiceOS</span>
  </footer>
</template>
