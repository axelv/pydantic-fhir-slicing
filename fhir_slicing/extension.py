from dataclasses import fields
from typing import (
    Any,
    LiteralString,
    Mapping,
)

from .base import BaseModel
from .element_array import BaseElementArray
from .utils import get_source_type, get_value_from_literal


class BaseExtension[TUrl: LiteralString](BaseModel):
    url: TUrl

    @classmethod
    def get_url(cls) -> str:
        """Get the url of the extension"""
        url = get_value_from_literal(cls.model_fields["url"].annotation)
        assert isinstance(url, str), f"Expected url to be a string, got {url}"
        return url


class GeneralExtension(BaseExtension):
    model_config = {"extra": "allow"}


class BaseSimpleExtension[TUrl: LiteralString](BaseExtension[TUrl]):
    url: TUrl

    @property
    def value(self):
        value_field_name = next(field.name for field in fields(self) if field.name.startswith("value"))
        return getattr(self, value_field_name)


class BaseExtensionArray(BaseElementArray[BaseExtension]):
    @classmethod
    def get_url(cls, value: Mapping) -> str | None:
        """Get the url of the extension"""
        return value.get("url", None)

    @classmethod
    def discriminator(cls, value: Any) -> str:
        url = cls.get_url(value)
        for slice_name, slice_annotation in cls.get_slice_annotations().items():
            for source_type in get_source_type(slice_annotation, expect=BaseExtension):
                if source_type.get_url() == url:
                    return slice_name
        return "@default"


if __name__ == "__main__":
    pass
