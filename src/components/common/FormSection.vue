<script setup lang="ts">
interface Props {
  title?: string
  description?: string
}

withDefaults(defineProps<Props>(), {
  title: undefined,
  description: undefined,
})
</script>

<template>
  <div class="space-y-4">
    <div v-if="title || description" class="border-b border-border-light pb-4">
      <h3 v-if="title" class="text-base font-medium text-neutral-800">{{ title }}</h3>
      <p v-if="description" class="text-sm text-neutral-600 mt-1">{{ description }}</p>
    </div>
    <div class="space-y-4">
      <slot />
    </div>
  </div>
</template>
