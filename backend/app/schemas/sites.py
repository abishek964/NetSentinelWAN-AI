from pydantic import BaseModel


class SiteOut(BaseModel):
    site_id: int
    site_name: str
