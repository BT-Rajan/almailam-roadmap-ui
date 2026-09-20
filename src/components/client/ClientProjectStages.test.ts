import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { describe, expect, it } from 'vitest'

import ClientProjectStages from '@/components/client/ClientProjectStages.vue'
import { i18n } from '@/i18n'
import { fixture } from '@/test-utils/mockApi'
import type { Project } from '@/types/Project'

const project = (index: number, overrides: Partial<Project> = {}): Project =>
  ({
    ...fixture.project,
    id: `P-${index}`,
    projectNo: `26000${String(index).padStart(2, '0')}`,
    projectName: `Project ${index}`,
    ...overrides,
  }) as Project

function mountStages(projects: Project[]) {
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(ClientProjectStages, { props: { projects }, global: { plugins: [pinia, i18n] } })
}

describe('ClientProjectStages (client overview)', () => {
  it('shows, per project, the stage it is at', () => {
    const wrapper = mountStages([
      project(1, { currentStage: 'Quotation', status: 'Active' }),
      project(2, { currentStage: 'Design', status: 'Active' }),
    ])
    const cards = wrapper.findAll('h3')
    expect(cards.map((h) => h.text())).toEqual(['Project 2', 'Project 1']) // newest first
    const text = wrapper.text()
    expect(text).toMatch(/Currently at\s*Design/)
    expect(text).toMatch(/Currently at\s*Quotation/)
  })

  it('opens a project from its button', async () => {
    const wrapper = mountStages([project(1)])
    await wrapper.findAll('button').find((b) => b.text() === 'Open project')!.trigger('click')
    expect(wrapper.emitted('open')).toEqual([['P-1']])
  })

  it('opens the project at a stage when that stage is clicked in its stepper', async () => {
    const wrapper = mountStages([project(1, { currentStage: 'Quotation' })])
    const stageButton = wrapper.findAll('button').find((b) => b.text().includes('Contract'))
    expect(stageButton).toBeTruthy()
    await stageButton!.trigger('click')
    const [projectId, tab] = wrapper.emitted('open')![0]
    expect(projectId).toBe('P-1')
    expect(tab).toBe('contract')
  })

  it('pages through more projects than fit on a page', async () => {
    const wrapper = mountStages(Array.from({ length: 7 }, (_, index) => project(index + 1)))
    expect(wrapper.findAll('h3')).toHaveLength(5)
    await wrapper.find('button[aria-label="Go to page 2"]').trigger('click')
    expect(wrapper.findAll('h3')).toHaveLength(2)
  })
})
