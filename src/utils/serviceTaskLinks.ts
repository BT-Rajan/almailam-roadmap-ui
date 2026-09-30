import type { Project } from '@/types/Project'
import type { Task } from '@/types/Task'

// One project "service" a task can hang off -- a selected Design
// activity, Permit, or Supervision activity (the same three rows
// project_service._create_service_tasks auto-creates one task for).
// Shared by ServiceTasksDialog.vue, ProjectTasksTab.vue and the
// Overview tab so a service's system-created tasks and the ones staff
// add by hand always live in one list.
export type ServiceKind = 'design' | 'permit' | 'supervision'

export interface ServiceRef {
  kind: ServiceKind
  // The project's own selected-row id (SelectedServiceActivity.id /
  // SelectedPermit.id / SelectedSupervisionActivity.id), not the catalog id.
  id: string
  name: string
  status?: string
}

export function serviceKey(kind: ServiceKind, id: string): string {
  return `${kind}:${id}`
}

// Which service a task is linked to, as a serviceKey -- undefined for
// a plain, unlinked task.
export function taskServiceKey(task: Task): string | undefined {
  if (task.selectedActivityId) return serviceKey('design', task.selectedActivityId)
  if (task.selectedPermitId) return serviceKey('permit', task.selectedPermitId)
  if (task.selectedSupervisionActivityId) return serviceKey('supervision', task.selectedSupervisionActivityId)
  return undefined
}

export function taskBelongsTo(task: Task, service: ServiceRef | null): boolean {
  const key = taskServiceKey(task)
  return service ? key === serviceKey(service.kind, service.id) : key === undefined
}

// The create-payload fields that link a new task to `service` (none
// for a general task).
export function serviceLinkFields(service: ServiceRef | null): Pick<Task, 'selectedActivityId' | 'selectedPermitId' | 'selectedSupervisionActivityId'> {
  return {
    selectedActivityId: service?.kind === 'design' ? service.id : undefined,
    selectedPermitId: service?.kind === 'permit' ? service.id : undefined,
    selectedSupervisionActivityId: service?.kind === 'supervision' ? service.id : undefined,
  }
}

// Every service on this project that tasks can be linked to, in the
// order the Overview shows them. Rows without an id yet (not persisted)
// are skipped -- nothing can link to them.
export function projectServices(project: Project, kinds: ServiceKind[] = ['design', 'permit', 'supervision']): ServiceRef[] {
  const services: ServiceRef[] = []
  if (kinds.includes('design')) {
    for (const activity of project.selectedActivities ?? []) {
      if (activity.id) services.push({ kind: 'design', id: activity.id, name: activity.activityName, status: activity.status ?? 'Not Started' })
    }
  }
  if (kinds.includes('permit')) {
    for (const permit of project.selectedPermits ?? []) {
      services.push({ kind: 'permit', id: permit.id, name: permit.permitName, status: permit.status })
    }
  }
  if (kinds.includes('supervision')) {
    for (const activity of project.selectedSupervisionActivities ?? []) {
      if (activity.id) services.push({ kind: 'supervision', id: activity.id, name: activity.activityName, status: activity.status })
    }
  }
  return services
}

export interface TaskProgress {
  done: number
  total: number
}

// Done/total task counts per serviceKey, plus '' for unlinked tasks.
export function taskProgressByService(tasks: Task[]): Record<string, TaskProgress> {
  const progress: Record<string, TaskProgress> = {}
  for (const task of tasks) {
    const key = taskServiceKey(task) ?? ''
    const entry = (progress[key] ??= { done: 0, total: 0 })
    entry.total += 1
    if (task.status === 'Completed') entry.done += 1
  }
  return progress
}
