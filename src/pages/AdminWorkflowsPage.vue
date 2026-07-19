<script setup lang="ts">
import { computed, onMounted } from 'vue'

import BaseButton from '@/components/common/BaseButton.vue'
import Card from '@/components/common/Card.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import SkeletonLoader from '@/components/common/SkeletonLoader.vue'
import Stepper from '@/components/common/Stepper.vue'
import WorkflowCard from '@/components/administration/WorkflowCard.vue'
import WorkflowStageEditor from '@/components/administration/WorkflowStageEditor.vue'
import { useToastStore } from '@/stores/toastStore'
import { useWorkflowStore } from '@/stores/workflowStore'

const workflowStore = useWorkflowStore()
const toastStore = useToastStore()

const stepperSteps = computed(() => (workflowStore.selectedTemplate?.stages ?? []).map((stage) => ({ label: stage.name })))

function loadData(): void {
  workflowStore.loadTemplates()
}

onMounted(() => {
  if (workflowStore.templates.length === 0) loadData()
})

function handleSave(): void {
  toastStore.show('success', 'Workflow updated', `${workflowStore.selectedTemplate?.name} has been saved.`)
}

function handleSetDefault(): void {
  if (!workflowStore.selectedTemplate) return
  workflowStore.setDefaultTemplate(workflowStore.selectedTemplate.id)
  toastStore.show('info', 'Default workflow changed', `${workflowStore.selectedTemplate.name} is now the default.`)
}
</script>

<template>
  <div class="flex flex-col gap-6 p-4 lg:p-6">
    <PageHeader title="Workflow Configuration" subtitle="Define and adjust the project workflow stages." />

    <ErrorState v-if="workflowStore.error" :description="workflowStore.error" @retry="loadData" />

    <div v-else-if="workflowStore.isLoading" class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="rounded-xl border border-border-light bg-bg-card p-5">
        <SkeletonLoader :rows="5" />
      </div>
      <div class="rounded-xl border border-border-light bg-bg-card p-5 laptop:col-span-2">
        <SkeletonLoader :rows="8" />
      </div>
    </div>

    <div v-else class="grid grid-cols-1 gap-6 laptop:grid-cols-3">
      <div class="flex flex-col gap-3">
        <WorkflowCard
          v-for="template in workflowStore.templates"
          :key="template.id"
          :template="template"
          :active="template.id === workflowStore.selectedTemplateId"
          @select="workflowStore.selectTemplate"
        />
      </div>

      <div class="flex flex-col gap-6 laptop:col-span-2">
        <EmptyState v-if="!workflowStore.selectedTemplate" title="Select a workflow template" description="Choose a template on the left to view and edit its stages." />

        <template v-else>
          <Card>
            <template #header>
              <h3 class="text-sm font-semibold text-neutral-800">Workflow Visualization</h3>
            </template>
            <div class="overflow-x-auto pb-1">
              <div class="min-w-[640px]">
                <Stepper :steps="stepperSteps" :current-step="-1" />
              </div>
            </div>
          </Card>

          <Card>
            <template #header>
              <div class="flex items-center justify-between gap-3">
                <h3 class="text-sm font-semibold text-neutral-800">{{ workflowStore.selectedTemplate.name }} Stages</h3>
                <div class="flex items-center gap-2">
                  <BaseButton
                    v-if="!workflowStore.selectedTemplate.isDefault"
                    variant="secondary"
                    size="sm"
                    @click="handleSetDefault"
                  >
                    Set as Default
                  </BaseButton>
                  <BaseButton size="sm" @click="handleSave">Save Changes</BaseButton>
                </div>
              </div>
            </template>

            <WorkflowStageEditor
              :stages="workflowStore.selectedTemplate.stages"
              @update="workflowStore.updateStage"
              @remove="workflowStore.removeStage"
              @move="workflowStore.moveStage"
              @add="workflowStore.addStage"
            />
          </Card>
        </template>
      </div>
    </div>
  </div>
</template>
