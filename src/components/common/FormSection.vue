<script setup lang="ts">
interface Props {
  title?: string
  description?: string
  required?: boolean
}

withDefaults(defineProps<Props>(), {
  title: undefined,
  description: undefined,
  required: false,
})
</script>

<template>
  <div class="space-y-4">
    <div v-if="title || description" class="border-b border-border-light pb-4">
      <h3 v-if="title" class="text-base font-medium text-text-primary">
        {{ title }}
        <span v-if="required" class="text-danger-500">*</span>
      </h3>
      <p v-if="description" class="text-sm text-text-secondary mt-1">{{ description }}</p>
    </div>
    <div class="space-y-4">
      <slot />
    </div>
  </div>
</template>
