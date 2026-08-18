from pydantic import BaseModel

SEARCH_CATEGORIES = ("Client", "Project", "Document", "Form", "Task", "User")


class SearchResult(BaseModel):
    id: str
    category: str
    title: str
    subtitle: str
    routeName: str
    params: dict[str, str] | None = None
