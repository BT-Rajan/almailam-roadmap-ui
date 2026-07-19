import { ROUTE_NAMES } from '@/constants/routeNames'
import { CLIENTS } from '@/mock/clients'
import { DOCUMENTS } from '@/mock/documents'
import { GOVERNMENT_FORMS } from '@/mock/governmentForms'
import { PROJECTS } from '@/mock/projects'
import { TASKS } from '@/mock/tasks'
import { USERS } from '@/mock/users'
import type { SearchResult } from '@/types/Search'
import { simulateNetworkDelay } from '@/utils/mockDelay'

const RESULTS_PER_CATEGORY = 5

function matches(term: string, ...fields: string[]): boolean {
  return fields.some((field) => field.toLowerCase().includes(term))
}

function clientNameFor(clientId: string): string {
  return CLIENTS.find((client) => client.id === clientId)?.companyName ?? ''
}

async function search(query: string): Promise<SearchResult[]> {
  await simulateNetworkDelay(150)

  const term = query.trim().toLowerCase()
  if (term.length === 0) return []

  const projectResults: SearchResult[] = PROJECTS.filter((project) =>
    matches(term, project.projectName, project.projectNo, clientNameFor(project.clientId)),
  )
    .slice(0, RESULTS_PER_CATEGORY)
    .map((project) => ({
      id: project.id,
      category: 'Project',
      title: project.projectName,
      subtitle: `${project.projectNo} · ${clientNameFor(project.clientId)}`,
      routeName: ROUTE_NAMES.PROJECT_WORKSPACE,
      params: { projectId: project.id },
    }))

  const documentResults: SearchResult[] = DOCUMENTS.filter((document) =>
    matches(term, document.title, document.type, document.uploadedBy),
  )
    .slice(0, RESULTS_PER_CATEGORY)
    .map((document) => ({
      id: document.id,
      category: 'Document',
      title: document.title,
      subtitle: `${document.type} · ${document.revision}`,
      routeName: ROUTE_NAMES.DOCUMENT_VIEWER,
      params: { documentId: document.id },
    }))

  const formResults: SearchResult[] = GOVERNMENT_FORMS.filter((form) =>
    matches(term, form.title, form.formCode, form.category),
  )
    .slice(0, RESULTS_PER_CATEGORY)
    .map((form) => ({
      id: form.id,
      category: 'Form',
      title: form.title,
      subtitle: `${form.formCode} · ${form.category}`,
      routeName: ROUTE_NAMES.GOVERNMENT_FORMS,
    }))

  const taskResults: SearchResult[] = TASKS.filter((task) => matches(term, task.title, task.assignedTo, task.status))
    .slice(0, RESULTS_PER_CATEGORY)
    .map((task) => ({
      id: task.id,
      category: 'Task',
      title: task.title,
      subtitle: `${task.assignedTo} · ${task.status}`,
      routeName: ROUTE_NAMES.TASKS,
    }))

  const userResults: SearchResult[] = USERS.filter((user) => matches(term, user.name, user.designation, user.role))
    .slice(0, RESULTS_PER_CATEGORY)
    .map((user) => ({
      id: user.id,
      category: 'User',
      title: user.name,
      subtitle: `${user.designation} · ${user.role}`,
      routeName: ROUTE_NAMES.ADMIN_USERS,
    }))

  return [...projectResults, ...documentResults, ...formResults, ...taskResults, ...userResults]
}

export const searchService = {
  search,
}
