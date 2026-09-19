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
    class="rounded-xl border border-border-light bg-bg-card shadow-glass-sm transition-[box-shadow,border-color,transform] duration-normal"
    :class="[
      hoverable ? 'hover:-translate-y-px hover:border-accent-400/40 hover:shadow-glass' : '',
      // Edge-to-edge content (tables, lists) would otherwise paint square
      // corners/row hovers over the card's rounded border and look like it
      // bleeds out -- clip it. Padded cards keep overflow visible so
      // dropdowns/popovers inside them aren't cut off.
      padded ? '' : 'overflow-hidden',
    ]"
  >
    <div v-if="$slots.header" class="rounded-t-xl border-b border-border-light px-5 py-4">
      <slot name="header" />
    </div>
    <div :class="padded ? 'p-5' : ''">
      <slot />
    </div>
    <div v-if="$slots.footer" class="rounded-b-xl border-t border-border-light px-5 py-4">
      <slot name="footer" />
    </div>
  </div>
</template>
