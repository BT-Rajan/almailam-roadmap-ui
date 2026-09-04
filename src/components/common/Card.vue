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
    class="rounded-xl border border-border-light bg-bg-card shadow-glass-sm transition-[box-shadow,border-color] duration-normal"
    :class="hoverable ? 'hover:border-accent-400/40 hover:shadow-glass' : ''"
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
