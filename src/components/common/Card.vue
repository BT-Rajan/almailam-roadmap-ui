<script setup lang="ts">
interface Props {
  padded?: boolean
  hoverable?: boolean
}

withDefaults(defineProps<Props>(), {
  padded: true,
  hoverable: false,
})
</script>

<template>
  <div
    class="rounded-xl border border-border-light bg-bg-card shadow-soft transition-shadow duration-normal"
    :class="hoverable ? 'hover:shadow-medium' : ''"
  >
    <div v-if="$slots.header" class="border-b border-border-light px-5 py-4">
      <slot name="header" />
    </div>
    <div :class="padded ? 'p-5' : ''">
      <slot />
    </div>
    <div v-if="$slots.footer" class="border-t border-border-light px-5 py-4">
      <slot name="footer" />
    </div>
  </div>
</template>
