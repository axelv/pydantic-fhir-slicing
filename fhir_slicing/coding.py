from typing import Literal, Protocol

from fhir_slicing.typing import Omissible

from .base import BaseModel


class BaseCoding[TSystem: str](BaseModel):
    system: TSystem


class GeneralCoding(BaseCoding):
    display: Omissible[str] = None
    code: str
    model_config = {"extra": "allow"}


class CodingProtocol[TSystem: str](Protocol):
    @property
    def system(self) -> TSystem: ...

    @property
    def code(self) -> str: ...

    @classmethod
    def get_system(cls) -> TSystem | None: ...


class SCTCoding(BaseCoding):
    system: Literal["http://snomed.info/sct"] = "http://snomed.info/sct"
    code: str
    display: str


class LOINCCoding(BaseCoding):
    system: Literal["http://loinc.org"] = "http://loinc.org"
    code: str
    display: str
