from typing import Any, Mapping, Type

from .base import BaseModel
from .coding import BaseCoding
from .element_array import BaseElementArray
from .utils import get_source_type, get_value_from_literal


class UsageCoding[TSystem: str, TCode: str, TVersion: str | None](BaseCoding[TSystem]):
    code: TCode
    version: TVersion | None = None

    def __eq__(self, other: object):
        if not isinstance(other, UsageCoding):
            return False
        return hash((self.system, self.code, self.version)) == hash((other.system, other.code, other.version))

    @classmethod
    def get_code(cls):
        """Get the coding representation"""
        system: TSystem | None = cls.get_system()
        code: TCode | None = get_value_from_literal(cls.model_fields["code"].annotation)  # type: ignore[override]
        version: TVersion | None = get_value_from_literal(cls.model_fields["version"].annotation)  # type: ignore[override]
        if system is None or code is None:
            return None
        return UsageCoding(system=system, code=code, version=version)


class BaseUsageContext[TUsageCoding: UsageCoding](BaseModel):
    code: TUsageCoding
    model_config = {"extra": "allow"}

    @classmethod
    def get_code(cls) -> TUsageCoding | None:
        """Get the coding representation"""
        code_model: Type[TUsageCoding] = cls.model_fields["code"].annotation  # type: ignore[override]
        usage_code: TUsageCoding | None = code_model.get_code()  # type: ignore[override]
        return usage_code


class BaseUsageContextArray(BaseElementArray[BaseUsageContext]):
    @classmethod
    def get_code(cls, value: Mapping) -> UsageCoding | None:
        """Return the code of the usage context."""
        return value.get("code", None)

    @classmethod
    def discriminator(cls, value: Any) -> str | None:
        coding = cls.get_code(value)
        for slice_name, slice_annotation in cls.get_slice_annotations().items():
            for source_type in get_source_type(slice_annotation, expect=BaseUsageContext):
                if slice_name == "@default" or source_type.get_code() == coding:
                    return slice_name
        return "@default"
