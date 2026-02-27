from typing import List, Union, Optional
from pydantic import BaseModel, Field

class PanelField(BaseModel):
    InternalName: str
    Type: str  # "Text" or "Number"
    TextValue: Optional[str] = Field(default=None)
    NumberValue: Optional[Union[float, int]] = Field(default=None)

class EstudioTitulosPlano(BaseModel):
    PanelFields: List[PanelField]

class MinutaCancelacionPlano(BaseModel):
    PanelFields: List[PanelField]

class MinutaConstitucionPlano(BaseModel):
    PanelFields: List[PanelField]