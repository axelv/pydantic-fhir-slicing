import inspect
from dataclasses import fields
from typing import (
    Any,
    Literal,
    LiteralString,
    TypeVar,
    get_args,
    get_origin,
)

from pydantic import BaseModel

from .element_array import BaseElementArray
from .utils import get_source_type

TUrl = TypeVar("TUrl", bound=LiteralString)


class BaseExtension[TUrl](BaseModel):
    url: TUrl

    @classmethod
    def get_url(cls) -> str:
        url_type = cls.model_fields["url"].annotation
        if get_origin(url_type) is not Literal:
            raise ValueError(f"Cannot determine url from non-literal type in {cls}")
        url = get_args(url_type)[0]
        assert isinstance(url, str), f"Expected url to be a string, got {url}"
        return url


class GeneralExtension(BaseExtension):
    model_config = {"extra": "allow"}


class BaseSimpleExtension[TUrl](BaseExtension[TUrl]):
    url: TUrl

    @property
    def value(self):
        value_field_name = next(field.name for field in fields(self) if field.name.startswith("value"))
        return getattr(self, value_field_name)


TExtension = TypeVar("TExtension", bound=BaseSimpleExtension)


class BaseExtensionArray(BaseElementArray[BaseExtension]):
    @classmethod
    def get_url(cls, value: dict | BaseExtension) -> str | None:
        """Get the url of the extension"""
        if isinstance(value, dict):
            return value.get("url", None)
        if isinstance(value, BaseExtension):
            return value.url
        return None

    @classmethod
    def discriminator(cls, value: Any) -> str:
        url = cls.get_url(value)
        for slice_name, slice_annotation in cls.get_slice_annotations().items():
            for source_type in get_source_type(slice_annotation):
                is_class = inspect.isclass(source_type)
                is_extension = is_class and issubclass(source_type, BaseExtension)
                is_not_general_extension = is_extension and not issubclass(source_type, GeneralExtension)
                if is_not_general_extension and source_type.get_url() == url:
                    return slice_name
        return "@default"


if __name__ == "__main__":
    pass
