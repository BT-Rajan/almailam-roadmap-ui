<script setup lang="ts">
interface Props {
  title: string
  subtitle?: string
}

withDefaults(defineProps<Props>(), {
  subtitle: undefined,
})
</script>

<template>
  <div class="flex min-h-[calc(100vh-64px)] items-center justify-center px-4 py-12 tablet:py-16">
    <div class="w-full max-w-md">
      <div class="glass-panel rounded-xl p-6 shadow-glass tablet:p-8">
        <div class="mb-6">
          <h1 class="text-2xl font-bold text-neutral-900 tablet:text-3xl">{{ title }}</h1>
          <p v-if="subtitle" class="mt-2 text-sm text-neutral-600">{{ subtitle }}</p>
        </div>

        <slot />

        <div v-if="$slots.footer" class="mt-5">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </div>
</template>
