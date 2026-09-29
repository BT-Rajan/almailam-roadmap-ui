import { describe, expect, it } from 'vitest'
import { nextTick, reactive, ref } from 'vue'

import { useRevealedErrors, useRevealedRowErrors } from '@/composables/useRevealedErrors'

describe('useRevealedErrors', () => {
  it('hides untouched errors, shows edited fields, and everything after reveal', async () => {
    const source = ref<Record<string, string>>({ name: 'Required', email: 'Required' })
    const shown = useRevealedErrors(() => source.value)
    expect(shown.errors.value).toEqual({})

    source.value = { name: 'Required', email: 'Enter a valid email' }
    await nextTick()
    expect(shown.errors.value).toEqual({ email: 'Enter a valid email' })

    shown.reveal()
    expect(shown.errors.value).toEqual({ name: 'Required', email: 'Enter a valid email' })
  })

  it('does not flag fields that only appear because of another choice', async () => {
    const source = ref<Record<string, string>>({ fullName: 'Required' })
    const shown = useRevealedErrors(() => source.value)
    source.value = { legalName: 'Required' }
    await nextTick()
    expect(shown.errors.value).toEqual({})
  })

  it('starts over on reset', async () => {
    const source = ref<Record<string, string>>({ name: 'Required' })
    const shown = useRevealedErrors(() => source.value)
    shown.reveal()
    shown.reset()
    expect(shown.errors.value).toEqual({})
  })
})

describe('useRevealedRowErrors', () => {
  it('shows a row only once that row was edited', async () => {
    const rows = reactive([{ description: '' }, { description: '' }])
    const errors = () => rows.map((row) => (row.description ? {} : { description: 'Required' }))
    const shown = useRevealedRowErrors(() => rows, errors)
    expect(shown.errors.value).toEqual([{}, {}])

    rows[1].description = 'x'
    await nextTick()
    rows[1].description = ''
    await nextTick()
    expect(shown.errors.value).toEqual([{}, { description: 'Required' }])

    rows.push({ description: '' })
    await nextTick()
    expect(shown.errors.value[2]).toEqual({})

    shown.reveal()
    expect(shown.errors.value).toEqual([{ description: 'Required' }, { description: 'Required' }, { description: 'Required' }])
  })
})
