<script setup lang="ts">
interface Props {
  title: string
  description?: string
  fullWidth?: boolean
}

withDefaults(defineProps<Props>(), {
  description: undefined,
  fullWidth: false,
})
</script>

<template>
  <div class="space-y-4">
    <div>
      <h2 class="text-xl font-semibold text-neutral-900">{{ title }}</h2>
      <p v-if="description" class="text-sm text-neutral-600 mt-1">{{ description }}</p>
    </div>
    <div :class="fullWidth ? 'w-full' : 'grid grid-cols-1 tablet:grid-cols-2 gap-4'">
      <slot />
    </div>
  </div>
</template>
