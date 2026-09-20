import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { describe, expect, it } from 'vitest'
import { defineComponent, h } from 'vue'
import type { Component } from 'vue'

import PaginatedListComponent from '@/components/common/PaginatedList.vue'
import { i18n } from '@/i18n'

// The component is generic; h() only needs it as a plain component.
const PaginatedList = PaginatedListComponent as unknown as Component

const numbers = (count: number) => Array.from({ length: count }, (_, index) => index + 1)

function mountList(items: number[], props: Record<string, unknown> = {}) {
  const Host = defineComponent({
    props: { items: { type: Array as () => number[], required: true } },
    setup(hostProps) {
      return () =>
        h(PaginatedList, { items: hostProps.items, ...props }, {
          default: ({ items: page }: { items: number[] }) => h('ul', page.map((n) => h('li', { class: 'row' }, String(n)))),
        })
    },
  })
  // TablePagination reads the locale store (for RTL chevrons).
  const pinia = createPinia()
  setActivePinia(pinia)
  return mount(Host, { props: { items }, global: { plugins: [pinia, i18n] } })
}

const rows = (w: ReturnType<typeof mount>) => w.findAll('li.row').map((li) => li.text())
const pager = (w: ReturnType<typeof mount>) => w.find('nav')

describe('PaginatedList', () => {
  it('shows one page of items and a pager for a long list', () => {
    const w = mountList(numbers(12), { pageSize: 5 })
    expect(rows(w)).toEqual(['1', '2', '3', '4', '5'])
    expect(pager(w).exists()).toBe(true)
    expect(w.text()).toContain('12')
  })

  it('moves to the next page', async () => {
    const w = mountList(numbers(12), { pageSize: 5 })
    await w.find('button[aria-current="page"] + button').trigger('click')
    expect(rows(w)).toEqual(['6', '7', '8', '9', '10'])
  })

  it('has no pager when the list fits the smallest page size', () => {
    const w = mountList(numbers(4), { pageSize: 5 })
    expect(rows(w)).toEqual(['1', '2', '3', '4'])
    expect(pager(w).exists()).toBe(false)
  })

  it('shows everything on one page when the page size covers the list, but still offers a pager', () => {
    const w = mountList(numbers(8), { pageSize: 10 })
    expect(rows(w)).toHaveLength(8)
    expect(pager(w).exists()).toBe(true)
  })

  it('renders nothing extra for an empty list', () => {
    const w = mountList([])
    expect(rows(w)).toEqual([])
    expect(pager(w).exists()).toBe(false)
  })

  it('steps back to the last page when the list shrinks under the reader', async () => {
    const w = mountList(numbers(12), { pageSize: 5 })
    await w.findAll('button').find((b) => b.attributes('aria-label')?.includes('3'))?.trigger('click')
    expect(rows(w)).toEqual(['11', '12'])
    await w.setProps({ items: numbers(6) })
    expect(rows(w)).toEqual(['6'])
  })
})
