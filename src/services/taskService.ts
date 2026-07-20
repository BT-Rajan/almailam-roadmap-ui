import { TASKS } from '@/mock/tasks'
import type { Task } from '@/types/Task'
import { simulateNetworkDelay } from '@/utils/mockDelay'

async function getTasks(): Promise<Task[]> {
  await simulateNetworkDelay()
  return TASKS
}

async function getTaskById(taskId: string): Promise<Task | undefined> {
  await simulateNetworkDelay()
  return TASKS.find((task) => task.id === taskId)
}

export const taskService = {
  getTasks,
  getTaskById,
}
