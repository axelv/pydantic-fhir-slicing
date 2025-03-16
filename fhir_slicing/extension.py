from typing import (
    Self,
    cast,
)

from fhir_slicing.utils import get_value_from_literal

from .base import BaseModel


class BaseExtension[TUrl: str](BaseModel):
    url: TUrl


class GeneralExtension(BaseExtension):
    model_config = {"extra": "allow"}


class BaseSimpleExtension[TUrl: str, TValue](BaseExtension[TUrl]):
    url: TUrl

    @classmethod
    def get_url(cls) -> TUrl:
        return cast(TUrl, get_value_from_literal(cls.model_fields["url"].annotation))

    @property
    def value(self) -> TValue:
        value_field_name = next(field_name for field_name in self.model_fields.keys() if field_name.startswith("value"))
        return getattr(self, value_field_name)

    @classmethod
    def from_value(cls, value: TValue) -> "Self":
        """Create an extension from a value"""
        value_field_name = next(field_name for field_name in cls.model_fields.keys() if field_name.startswith("value"))
        return cls(url=cls.get_url(), **{value_field_name: value})


if __name__ == "__main__":
    pass
