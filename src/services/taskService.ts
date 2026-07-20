import { TASKS } from '@/mock/tasks'
import type { Task } from '@/types/Task'
import { simulateNetworkDelay } from '@/utils/mockDelay'

export type TaskInput = Omit<Task, 'id'>

function nextTaskId(): string {
  const sequence = TASKS.length + 1
  return `TSK-2026-${String(100 + sequence)}`
}

async function getTasks(): Promise<Task[]> {
  await simulateNetworkDelay()
  return TASKS
}

async function getTaskById(taskId: string): Promise<Task | undefined> {
  await simulateNetworkDelay()
  return TASKS.find((task) => task.id === taskId)
}

async function createTask(input: TaskInput): Promise<Task> {
  await simulateNetworkDelay()
  const task: Task = { ...input, id: nextTaskId() }
  TASKS.push(task)
  return task
}

export const taskService = {
  getTasks,
  getTaskById,
  createTask,
}
