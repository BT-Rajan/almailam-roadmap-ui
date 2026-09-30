import { describe, expect, it } from 'vitest'

import { useFormValidation } from '@/composables/useFormValidation'

const required = (value: unknown) => (typeof value === 'string' && value.trim() ? true : 'Required')

function setup() {
  const validation = useFormValidation()
  validation.setRules({ title: [required], project: [required] })
  return validation
}

describe('useFormValidation: when errors are shown', () => {
  it('keeps a blank form clean while validating live', () => {
    const { errors, validateAll } = setup()
    const valid = validateAll({ title: '', project: '' }, { reveal: false })
    expect(valid).toBe(false)
    expect(errors).toEqual({})
  })

  it('shows a field once it was changed, and only that field', () => {
    const { errors, validateAll } = setup()
    validateAll({ title: '', project: '' }, { reveal: false })
    validateAll({ title: 'x', project: '' }, { reveal: false })
    validateAll({ title: '', project: '' }, { reveal: false })
    expect(errors).toEqual({ title: 'Required' })
  })

  it('shows every error on a save attempt', () => {
    const { errors, validateAll } = setup()
    validateAll({ title: '', project: '' }, { reveal: false })
    expect(validateAll({ title: '', project: '' })).toBe(false)
    expect(errors).toEqual({ title: 'Required', project: 'Required' })
  })

  it('clears a shown error as soon as the field is fixed', () => {
    const { errors, validateAll } = setup()
    validateAll({ title: '', project: '' })
    validateAll({ title: 'Done', project: '' }, { reveal: false })
    expect(errors).toEqual({ project: 'Required' })
  })

  it('still reveals by default, for forms that only validate on submit', () => {
    const { errors, validateAll } = setup()
    validateAll({ title: '', project: 'p' })
    expect(errors).toEqual({ title: 'Required' })
  })
})
