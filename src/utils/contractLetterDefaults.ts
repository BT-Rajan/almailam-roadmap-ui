import type { ContractTemplateKey, ContractFeeFrequency } from '@/types/Contract'

interface ContractLetterDefaults {
  scopeItemsAr: string[]
  scopeItemsEn: string[]
  paymentTermsAr: string[]
  paymentTermsEn: string[]
  feeFrequency: ContractFeeFrequency
}

// Seed content matching the two source letters exactly (Arabic) with a
// parallel English translation, loaded into the New Contract form when
// a template is picked. Line order must stay in sync between the Ar/En
// arrays -- each index is the same line in both languages.
export const CONTRACT_LETTER_DEFAULTS: Record<ContractTemplateKey, ContractLetterDefaults> = {
  'design-and-permits': {
    scopeItemsAr: [
      '## المرحلة الأولى ( مرحلة التصميم)',
      'إعداد التصميم المعماري',
      'اعتماد المخطط المعماري من المالك.',
      'الحصول على موافقة وزارة الكهرباء والماء ( إمكانية إيصال تيار كهربائي)',
      '## المرحلة الثانية (التراخيص)',
      'الحصول على رخصة بناء / بلدية الكويت.',
    ],
    scopeItemsEn: [
      '## Phase 1 (Design Phase)',
      'Preparation of the architectural design',
      'Approval of the architectural plan by the owner.',
      'Obtaining approval from the Ministry of Electricity and Water (possibility of electrical power connection)',
      '## Phase 2 (Licensing)',
      'Obtaining a building permit from Kuwait Municipality.',
    ],
    paymentTermsAr: [
      'الدفعة الأولى 25% عند توقيع العقد.',
      'الدفعة الثانية 25% عند الإنتهاء من المرحلة الأولى.',
      'الدفعة الثالثة 50% عند الانتهاء من المرحلة الثانية.',
    ],
    paymentTermsEn: [
      'First installment 25% upon signing the contract.',
      'Second installment 25% upon completion of the first phase.',
      'Third installment 50% upon completion of the second phase.',
    ],
    feeFrequency: 'Lump Sum',
  },
  supervision: {
    scopeItemsAr: ['الإشراف على الهيكل الأسود يبدأ من إصدار تعهد الإشراف من البلدية'],
    scopeItemsEn: ['Supervision of the black structure (superstructure), starting from the issuance of the supervision undertaking by the Municipality'],
    paymentTermsAr: [],
    paymentTermsEn: [],
    feeFrequency: 'Monthly',
  },
}
