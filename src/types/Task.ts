export type TaskPriority = 'High' | 'Medium' | 'Low'

export type TaskSeverity = 'Critical' | 'Major' | 'Minor'

// 'Preset' is the initial status for a system-generated service task
// (one created automatically per selected Design activity/Permit/
// Supervision activity once a project leaves Contract -- see
// ProjectOverviewTab.vue's Design/Permit/Supervision-stage cards and
// projectService.closeDesignActivity/setPermitStatus/
// setSupervisionStatus) -- distinct from 'Pending', a manually-created
// task's own default. Graduates to 'Pending' the moment anything about
// it is edited (owner, dates, ...); the UI treats a task still sitting
// in 'Preset' as flagged, needing review.
export type TaskStatus = 'Preset' | 'Pending' | 'In Progress' | 'Completed'

export interface Task {
  id: string
  projectId: string
  title: string
  assignedTo: string
  priority: TaskPriority
  severity: TaskSeverity
  // When work on this task is meant to begin -- alongside dueDate/
  // dueTime below (when it's meant to be done by). Always set on an
  // auto-created service task (the project's own start date); optional
  // on a manually-created one.
  startDate?: string
  dueDate: string
  dueTime: string
  status: TaskStatus
  // The Design activity this task belongs to, if any -- closing every
  // task linked to the same activity auto-closes it (see
  // ProjectSelectedActivity.status in Project.ts). Undefined for a
  // plain, unlinked to-do -- the vast majority of tasks.
  selectedActivityId?: string
  // Same idea, for the Permit/Supervision activity this task belongs
  // to, if any -- see ProjectSelectedPermit/ProjectSelectedSupervisionActivity
  // in Project.ts. A task is linked to at most one of the three.
  selectedPermitId?: string
  selectedSupervisionActivityId?: string
}
