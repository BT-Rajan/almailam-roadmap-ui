from pydantic import BaseModel

SEARCH_CATEGORIES = (
    "Client",
    "Project",
    "Document",
    "Form",
    "Task",
    "User",
    "Contract",
    "Quotation",
    "Submission",
    "Payment",
)


class SearchResult(BaseModel):
    id: str
    category: str
    title: str
    subtitle: str
    routeName: str
    params: dict[str, str] | None = None
    # Query-string params for results that deep-link into a tab of another
    # page (e.g. a contract lives on the project workspace's Contract tab)
    # rather than having a standalone route of their own.
    query: dict[str, str] | None = None
