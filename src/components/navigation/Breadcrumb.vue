<script setup lang="ts">
import { ChevronRight } from '@lucide/vue'
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <nav
    v-if="route.meta.breadcrumbs?.length"
    aria-label="Breadcrumb"
    class="flex h-11 shrink-0 items-center gap-1.5 border-b border-[var(--color-border-default)] bg-[var(--color-bg-page)] px-4 text-sm lg:px-6"
  >
    <template v-for="(crumb, index) in route.meta.breadcrumbs" :key="`${crumb.label}-${index}`">
      <ChevronRight
        v-if="index > 0"
        :size="14"
        class="text-[var(--color-text-muted)]"
        aria-hidden="true"
      />
      <RouterLink
        v-if="crumb.routeName"
        :to="{ name: crumb.routeName }"
        class="text-[var(--color-text-secondary)] transition-colors duration-fast hover:text-[var(--color-text-primary)]"
      >
        {{ crumb.label }}
      </RouterLink>
      <span v-else class="font-medium text-[var(--color-text-primary)]">
        {{ crumb.label }}
      </span>
    </template>
  </nav>
</template>
