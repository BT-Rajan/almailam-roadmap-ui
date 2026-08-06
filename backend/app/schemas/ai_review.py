from pydantic import BaseModel


class ContractAISummaryOut(BaseModel):
    contractId: str
    summary: str
    details: str
    confidence: str
    suggestions: list[str]


class AIAssistantPromptIn(BaseModel):
    prompt: str
    provider: str | None = None
    template_name: str | None = None


class AIAssistantContractIn(BaseModel):
    contract_id: str


class AIAssistantDocumentIn(BaseModel):
    document_id: str


class AIAssistantRiskIn(BaseModel):
    entity_type: str
    entity_id: str


class AIInteractionOut(BaseModel):
    id: str
    prompt: str
    templateName: str | None = None
    provider: str
    summary: str
    details: str
    confidence: str
    suggestedActions: list[str]
    timestamp: str
