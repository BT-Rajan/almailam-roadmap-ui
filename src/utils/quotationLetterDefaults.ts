import type { QuotationTemplateKey, FeeFrequency } from '@/types/Quotation'

interface QuotationLetterDefaults {
  scopeItems: string[]
  paymentTerms: string[]
  feeFrequency: FeeFrequency
}

// Seed content matching the two source letters exactly. Loaded into the
// New Quotation form when a template is picked so staff start from the
// real wording and only need to adjust amounts/names, rather than
// retyping the whole scope/payment structure every time.
export const QUOTATION_LETTER_DEFAULTS: Record<QuotationTemplateKey, QuotationLetterDefaults> = {
  'design-and-permits': {
    scopeItems: [
      '## المرحلة الأولى ( مرحلة التصميم)',
      'إعداد التصميم المعماري',
      'اعتماد المخطط المعماري من المالك.',
      'الحصول على موافقة وزارة الكهرباء والماء ( إمكانية إيصال تيار كهربائي)',
      '## المرحلة الثانية (التراخيص)',
      'الحصول على رخصة بناء / بلدية الكويت.',
    ],
    paymentTerms: [
      'الدفعة الأولى 25% عند توقيع العقد.',
      'الدفعة الثانية 25% عند الإنتهاء من المرحلة الأولى.',
      'الدفعة الثالثة 50% عند الانتهاء من المرحلة الثانية.',
    ],
    feeFrequency: 'Lump Sum',
  },
  supervision: {
    scopeItems: ['الإشراف على الهيكل الأسود يبدأ من إصدار تعهد الإشراف من البلدية'],
    paymentTerms: [],
    feeFrequency: 'Monthly',
  },
}
