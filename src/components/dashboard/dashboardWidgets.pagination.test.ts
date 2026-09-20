import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { describe, expect, it } from 'vitest'

import RecentClientsWidget from '@/components/dashboard/RecentClientsWidget.vue'
import UpcomingDeadlinesWidget from '@/components/dashboard/UpcomingDeadlinesWidget.vue'
import { i18n } from '@/i18n'
import type { Deadline, RecentClient } from '@/types/Dashboard'

function plugins() {
  const pinia = createPinia()
  setActivePinia(pinia)
  return [pinia, i18n]
}

const clients = (count: number): RecentClient[] =>
  Array.from({ length: count }, (_, index) => ({
    id: `C-${index + 1}`,
    name: `Client ${index + 1}`,
    type: 'Company',
    status: 'Active',
    city: 'Kuwait City',
    // Later index = newer, so the list (newest first) starts at the highest number.
    createdDate: `2026-01-${String(index + 1).padStart(2, '0')}`,
  }))

const deadlines = (count: number): Deadline[] =>
  Array.from({ length: count }, (_, index) => ({
    id: `T-${index + 1}`,
    title: `Task ${index + 1}`,
    project: 'Project',
    dueDate: `2030-01-${String(index + 1).padStart(2, '0')}`,
    priority: 'medium',
    type: 'review',
  }))

describe('dashboard widgets are paginated instead of capped', () => {
  it('RecentClientsWidget pages through every client, not just the first few', async () => {
    const wrapper = mount(RecentClientsWidget, { props: { clients: clients(23), pageSize: 10 }, global: { plugins: plugins() } })
    expect(wrapper.findAll('li')).toHaveLength(10)
    expect(wrapper.text()).toContain('Client 23')
    expect(wrapper.text()).not.toContain('Client 13')

    // Third page holds the remaining three -- nothing is dropped.
    await wrapper.find('button[aria-label="Go to page 3"]').trigger('click')
    expect(wrapper.findAll('li')).toHaveLength(3)
    expect(wrapper.text()).toContain('Client 1')
  })

  it('RecentClientsWidget shows no pager when everything fits on one page', () => {
    const wrapper = mount(RecentClientsWidget, { props: { clients: clients(4) }, global: { plugins: plugins() } })
    expect(wrapper.findAll('li')).toHaveLength(4)
    expect(wrapper.find('nav').exists()).toBe(false)
  })

  it('UpcomingDeadlinesWidget keeps deadlines beyond the first page reachable, soonest first', async () => {
    const wrapper = mount(UpcomingDeadlinesWidget, { props: { deadlines: deadlines(12) }, global: { plugins: plugins() } })
    expect(wrapper.findAll('li')).toHaveLength(5)
    expect(wrapper.text()).toContain('Task 1')
    expect(wrapper.text()).not.toContain('Task 12')

    await wrapper.find('button[aria-label="Go to page 3"]').trigger('click')
    expect(wrapper.findAll('li')).toHaveLength(2)
    expect(wrapper.text()).toContain('Task 12')
  })
})
