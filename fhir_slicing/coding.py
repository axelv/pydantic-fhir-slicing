from typing import Any, Literal, Mapping, Protocol

from fhir_slicing.element_array import BaseElementArray
from fhir_slicing.utils import get_source_type, get_value_from_literal

from .base import BaseModel


class BaseCoding[TSystem: str](BaseModel):
    system: TSystem

    @classmethod
    def get_system(cls) -> TSystem | None:
        """Get the system of the coding"""
        system: TSystem | None = get_value_from_literal(cls.model_fields["system"].annotation)  # type: ignore[override]
        if system is None:
            return None
        assert isinstance(system, str), f"Expected system to be a string, got {system}"
        return system


class GeneralCoding(BaseCoding):
    display: str | None = None
    code: str
    model_config = {"extra": "allow"}


class CodingProtocol[TSystem: str](Protocol):
    @property
    def system(self) -> TSystem: ...

    @property
    def code(self) -> str: ...

    @classmethod
    def get_system(cls) -> TSystem | None: ...


class BaseCodingArray[TCoding: CodingProtocol = GeneralCoding](BaseElementArray[TCoding]):
    @classmethod
    def get_system(cls, value: Mapping) -> str | None:
        """Get the system of the coding"""
        return value.get("system", None)

    @classmethod
    def check_slice_annotations(cls):
        super().check_slice_annotations()

        # check if slices have unique systems
        system_slice_name_dict: dict[str | None, str] = dict()
        for slice_name, slice_annotation in cls.get_slice_annotations().items():
            for source_type in get_source_type(slice_annotation, expect=BaseCoding):
                system = source_type.get_system()
                if system in system_slice_name_dict:
                    existing_slice_name = system_slice_name_dict[system]
                    raise TypeError(
                        f"Duplicate discriminator value {system} for {source_type} with slice name {slice_name}. Slice '{existing_slice_name}' has claimed this system."
                    )
                system_slice_name_dict[system] = slice_name

    @classmethod
    def discriminator(cls, value: Any) -> str | None:
        """Get the discriminator value for a given value."""
        # Ex. sct, SCTCoding
        for slice_name, slice_annotation in cls.get_slice_annotations().items():
            for source_type in get_source_type(slice_annotation, expect=BaseCoding):
                if slice_name == "@default" or source_type.get_system() == cls.get_system(value):
                    return slice_name
        return "@default"


class SCTCoding(BaseCoding):
    system: Literal["http://snomed.info/sct"] = "http://snomed.info/sct"
    code: str
    display: str


class LOINCCoding(BaseCoding):
    system: Literal["http://loinc.org"] = "http://loinc.org"
    code: str
    display: str
