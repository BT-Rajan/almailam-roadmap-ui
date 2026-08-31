<script setup lang="ts">
import { Check, Copy, KeyRound } from '@lucide/vue'
import { ref, watch } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import BaseDialog from '@/components/common/BaseDialog.vue'
import IconButton from '@/components/common/IconButton.vue'

interface Props {
  modelValue: boolean
  userName: string
  password: string
  // Lets this same dialog double as the "here's the temporary password"
  // confirmation shown right after creating a new user, not just after
  // an explicit password reset -- the copy-once password box is
  // identical either way, only the heading differs.
  title?: string
  heading?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Password Reset',
  heading: undefined,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const copied = ref(false)

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) copied.value = false
  },
)

async function copyPassword(): Promise<void> {
  await navigator.clipboard.writeText(props.password)
  copied.value = true
}
</script>

<template>
  <BaseDialog
    :model-value="modelValue"
    :title="title"
    size="sm"
    :closable="false"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="flex flex-col items-center gap-3 py-2 text-center">
      <KeyRound class="h-12 w-12 shrink-0 text-success-500" />
      <h2 class="text-lg font-semibold text-text-primary">{{ heading ?? `Password reset for ${userName}` }}</h2>
      <p class="text-sm text-text-secondary">
        Share this new password with the user securely. It will not be shown again.
      </p>

      <div class="mt-2 flex w-full items-center justify-between gap-2 rounded-lg border border-border-default bg-bg-card px-4 py-3">
        <span class="select-all font-mono text-base tracking-wide text-text-primary">{{ password }}</span>
        <IconButton
          :icon="copied ? Check : Copy"
          :label="copied ? 'Copied' : 'Copy password'"
          size="sm"
          @click="copyPassword"
        />
      </div>
    </div>

    <template #footer>
      <BaseButton class="w-full" @click="emit('update:modelValue', false)">Done</BaseButton>
    </template>
  </BaseDialog>
</template>
