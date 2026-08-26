import type { GovernmentFormCategory, GovernmentFormLanguage } from '@/types/Government'

// Starter library of the government/legal forms the engineering office
// routinely issues to clients (design agreements, building-license
// undertakings, etc). Admins load whichever of these they want via the
// "Load Standard Forms" action on the Government Forms admin screen --
// nothing here is written to the backend until an admin picks it, and
// every field (template text, service tags, status) stays editable
// afterwards like any other form record.
export interface StandardGovernmentFormSeed {
  formCode: string
  title: string
  category: GovernmentFormCategory
  language: GovernmentFormLanguage
  description: string
  template: string
}

const SIGNATURE_BLOCK = `First Party (Engineering Office): {{companyName}}, signature: ………………
Second Party (Property Owner): {{clientName}}, signature: ………………
Date: {{date}}`

export const STANDARD_GOVERNMENT_FORMS: StandardGovernmentFormSeed[] = [
  {
    formCode: 'GF-01',
    title:
      'Design Agreement Contract – Agreement between the Engineering Office (First Party) and the Property Owner (Second Party) for design and licensing services',
    category: 'Agreement',
    language: 'English / Arabic',
    description:
      'Contract between the engineering office and the property owner covering design and licensing services for the project.',
    template: `This Design Agreement is made on {{date}} between {{companyName}} ("First Party", the Engineering Office) and {{clientName}} ("Second Party", the Property Owner), for the provision of design and licensing services for the project "{{projectName}}" located at {{projectAddress}}.

The First Party agrees to prepare and submit the architectural and structural design and to follow up licensing procedures with the relevant government authorities on behalf of the Second Party, in exchange for the agreed professional fees.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-02',
    title: 'Form No. 1 – New Building License Application',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Application submitted to the Municipality to obtain a new building license for the project.',
    template: `Application for a New Building License

Applicant / Property Owner: {{clientName}}
Project: {{projectName}}
Plot / Property Address: {{projectAddress}}
Supervising Engineering Office: {{companyName}}
Engineer in Charge: {{engineerName}}

The undersigned requests the issuance of a new building license for the above property, in accordance with the drawings and documents attached to this application.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-03',
    title: 'Form No. 2 – Undertaking on Compliance of Submitted Plans with Building Regulations',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking that the submitted architectural plans comply with current building regulations.',
    template: `Undertaking on Compliance with Building Regulations

I, {{clientName}}, owner of the property at {{projectAddress}} ("{{projectName}}"), undertake that the plans submitted with this application fully comply with the building regulations in force, and that {{companyName}} has verified this compliance prior to submission.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-04',
    title: 'Form No. 3 – Undertaking to Submit Structural Plans with Structural Design Safety Certification',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking to submit structural plans together with a structural design safety certificate.',
    template: `Undertaking to Submit Structural Plans with Safety Certification

I, {{clientName}}, undertake to submit the structural plans for "{{projectName}}" ({{projectAddress}}) together with a structural design safety certificate issued by a certified structural engineer, prior to the commencement of construction works.

Supervising Engineering Office: {{companyName}}

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-05',
    title: 'Form No. 4 – Undertaking to Provide Approvals from Relevant Government Authorities/Ministries',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking to obtain and provide all approvals required from relevant government authorities and ministries.',
    template: `Undertaking to Provide Government Authority Approvals

I, {{clientName}}, owner of "{{projectName}}" at {{projectAddress}}, undertake to obtain and provide all approvals required from the relevant government authorities and ministries prior to the issuance of the building license, and to bear full responsibility for any missing approval.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-06',
    title: 'Undertaking to Preserve and Comply with Ground Levels (first instance)',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking to preserve and comply with the approved ground levels for the plot.',
    template: `Undertaking to Preserve and Comply with Ground Levels

I, {{clientName}}, owner of the property at {{projectAddress}} ("{{projectName}}"), undertake to preserve and fully comply with the ground levels approved by the Municipality, and to bear responsibility for any deviation.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-07',
    title: 'Undertaking to Review the "To Whom It May Concern" Letter from the Public Authority for Housing Welfare',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking confirming review of the "To Whom It May Concern" letter issued by the Public Authority for Housing Welfare.',
    template: `Undertaking on Review of the Housing Welfare "To Whom It May Concern" Letter

I, {{clientName}}, confirm that I have reviewed the "To Whom It May Concern" letter issued by the Public Authority for Housing Welfare regarding the property at {{projectAddress}} ("{{projectName}}"), and undertake to comply with its content.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-08',
    title: 'Undertaking to Demolish and Remove Violations and Alterations',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking to demolish and remove any building violations or unauthorised alterations on the property.',
    template: `Undertaking to Demolish and Remove Violations

I, {{clientName}}, owner of the property at {{projectAddress}} ("{{projectName}}"), undertake to demolish and remove any violations or unauthorised alterations existing on the property, at my own expense and within the timeframe set by the Municipality.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-09',
    title: 'Undertaking of Responsibility for Property Inspection and Freedom from Violations',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking of responsibility for the inspection of the property and that it is free from violations.',
    template: `Undertaking of Responsibility for Property Inspection

I, {{clientName}}, undertake full responsibility for having inspected the property at {{projectAddress}} ("{{projectName}}") and confirm that it is free from any violations as of the date below.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-10',
    title: 'Structural Design Undertaking',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking regarding the safety and correctness of the structural design for the project.',
    template: `Structural Design Undertaking

{{companyName}} undertakes that the structural design prepared for "{{projectName}}" at {{projectAddress}} meets all applicable structural safety codes and standards, and takes full responsibility for the structural calculations submitted.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-11',
    title: 'Undertaking Not to Claim Property Valuation (due to height of surrounding buildings)',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking not to make any valuation claim arising from the height of surrounding buildings.',
    template: `Undertaking Not to Claim Property Valuation

I, {{clientName}}, owner of the property at {{projectAddress}} ("{{projectName}}"), undertake not to raise any claim for property valuation or compensation arising from the height of neighbouring buildings.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-12',
    title: 'Undertaking to Demolish the Property for Conversion to Investment Housing',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking to demolish the existing property in order to convert it to investment housing.',
    template: `Undertaking to Demolish for Conversion to Investment Housing

I, {{clientName}}, owner of the property at {{projectAddress}}, undertake to demolish the existing structure for the purpose of converting the property to investment housing under project "{{projectName}}", in accordance with the applicable regulations.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-13',
    title: 'Undertaking to Bear Responsibility for Removal of Debris and Construction Waste',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking to bear responsibility for the removal of debris and construction waste from the site.',
    template: `Undertaking on Removal of Debris and Construction Waste

I, {{clientName}}, undertake to bear full responsibility for the removal of debris and construction waste generated at {{projectAddress}} ("{{projectName}}"), and to dispose of it at designated locations only.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-14',
    title: 'Undertaking of Attachment/Joining Between Plots',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking regarding the attachment or joining of the property with an adjacent plot.',
    template: `Undertaking of Attachment/Joining Between Plots

I, {{clientName}}, owner of the property at {{projectAddress}} ("{{projectName}}"), undertake the terms of attachment/joining between this plot and the adjacent plot, and accept full responsibility arising from it.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-15',
    title: 'Undertaking Not to Demand Electrical Power Connection',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking not to demand an electrical power connection for the property.',
    template: `Undertaking Not to Demand Electrical Power Connection

I, {{clientName}}, owner of the property at {{projectAddress}} ("{{projectName}}"), undertake not to demand an electrical power connection until the conditions set by the Ministry of Electricity and Water are met.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-16',
    title: 'Undertaking Not to Rent Out or Subdivide the Property',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking not to rent out or subdivide the property into separate units without authorisation.',
    template: `Undertaking Not to Rent Out or Subdivide the Property

I, {{clientName}}, owner of the property at {{projectAddress}} ("{{projectName}}"), undertake not to rent out or subdivide the property into separate independent units without obtaining prior authorisation from the relevant authorities.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-17',
    title: 'Undertaking Not to Demand Services (electricity, telephone, sewage)',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking not to demand electricity, telephone, or sewage services until required conditions are met.',
    template: `Undertaking Not to Demand Services

I, {{clientName}}, owner of the property at {{projectAddress}} ("{{projectName}}"), undertake not to demand electricity, telephone, or sewage connection services until the conditions set by the relevant authorities are satisfied.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-18',
    title: 'Undertaking to Preserve Services (underground utilities)',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking to preserve existing underground utility services during construction.',
    template: `Undertaking to Preserve Underground Utility Services

I, {{clientName}}, undertake to preserve all existing underground utility services (water, electricity, telephone, sewage) at {{projectAddress}} ("{{projectName}}") during excavation and construction, and to bear responsibility for any damage caused to them.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-19',
    title: 'Undertaking to Preserve and Comply with Ground Levels (second instance)',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'A second, separately-tracked undertaking to preserve and comply with the approved ground levels.',
    template: `Undertaking to Preserve and Comply with Ground Levels

I, {{clientName}}, owner of the property at {{projectAddress}} ("{{projectName}}"), reaffirm my undertaking to preserve and fully comply with the ground levels approved by the Municipality throughout the construction works.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-20',
    title: 'Undertaking to Preserve Services and Reinforce Excavation Sides',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking to preserve nearby services and reinforce the sides of excavation works.',
    template: `Undertaking to Preserve Services and Reinforce Excavation Sides

I, {{clientName}}, undertake to preserve nearby services and to reinforce the sides of excavation at {{projectAddress}} ("{{projectName}}") to prevent collapse or damage to adjacent properties and utilities.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-21',
    title: 'Undertaking on the Correctness of Unit Numbering and Automated (Civil ID) Numbers',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking confirming the correctness of unit numbering and the automated Civil ID numbers used.',
    template: `Undertaking on Correctness of Unit Numbering

I, {{clientName}}, confirm the correctness of the unit numbering and the automated (Civil ID) numbers submitted for "{{projectName}}" at {{projectAddress}}, and bear responsibility for any discrepancy.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-22',
    title: 'Undertaking Not to Claim a Steam/Duct Space',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking not to claim additional steam duct or shaft space beyond what is approved.',
    template: `Undertaking Not to Claim a Steam/Duct Space

I, {{clientName}}, owner of the property at {{projectAddress}} ("{{projectName}}"), undertake not to claim any additional steam duct or shaft space beyond what has been approved in the design.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-23',
    title: 'Undertaking of Review of the Ownership Title Deed',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking confirming that the ownership title deed for the property has been reviewed.',
    template: `Undertaking on Review of the Ownership Title Deed

I, {{clientName}}, confirm that the ownership title deed for the property at {{projectAddress}} ("{{projectName}}") has been reviewed and is free of any dispute, and undertake to notify {{companyName}} of any change to its status.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-24',
    title: 'Undertaking to Bear Responsibility for Rented Shops/Units',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking to bear responsibility for existing rented shops or units on the property.',
    template: `Undertaking on Responsibility for Rented Shops/Units

I, {{clientName}}, owner of the property at {{projectAddress}} ("{{projectName}}"), undertake full responsibility for any existing tenancy of shops or units on the property and its effect on the licensing process.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-25',
    title: 'Undertaking to Remove the Electrical Cable',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking to remove or relocate an electrical cable affecting the property or works.',
    template: `Undertaking to Remove the Electrical Cable

I, {{clientName}}, undertake to remove/relocate the electrical cable affecting the property at {{projectAddress}} ("{{projectName}}"), at my own expense and in coordination with the Ministry of Electricity and Water.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-26',
    title: 'Undertaking on the Validity of Documents and Signatures',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Undertaking confirming the validity and authenticity of all documents and signatures submitted.',
    template: `Undertaking on the Validity of Documents and Signatures

I, {{clientName}}, undertake that all documents and signatures submitted in connection with "{{projectName}}" at {{projectAddress}} are valid, authentic, and legally binding, and accept full responsibility for any forgery or misrepresentation.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-27',
    title: 'Supervision Agreement',
    category: 'Agreement',
    language: 'English / Arabic',
    description: 'Agreement appointing the engineering office to supervise construction works for the project.',
    template: `This Supervision Agreement is made on {{date}} between {{companyName}} ("First Party", the Engineering Office) and {{clientName}} ("Second Party", the Property Owner), appointing the First Party to provide site supervision services for "{{projectName}}" at {{projectAddress}} under the direction of {{engineerName}}.

${SIGNATURE_BLOCK}`,
  },
  {
    formCode: 'GF-28',
    title: 'Form for Determining the Location of the House/Utility Connection',
    category: 'Legal Undertaking',
    language: 'Arabic',
    description: 'Form used to determine and confirm the precise location of the house or its utility connection point.',
    template: `Form for Determining the Location of the House/Utility Connection

Property: {{projectAddress}} ("{{projectName}}")
Owner: {{clientName}}
Supervising Engineering Office: {{companyName}}

This form confirms the precise location of the house and/or its utility connection point on the plot, as surveyed and marked by {{engineerName}}.

${SIGNATURE_BLOCK}`,
  },
]
