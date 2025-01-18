import inspect
from dataclasses import dataclass, fields
from typing import (
    Annotated,
    Any,
    Literal,
    LiteralString,
    TypeVar,
    get_args,
    get_origin,
)

from pydantic import BaseModel

from element_array import BaseElementArray
from utils import Cardinality, get_source_type

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


@dataclass(kw_only=True)
class BaseExtensionArray(BaseElementArray[BaseExtension, GeneralExtension]):
    other: Annotated[list[GeneralExtension] | None, Cardinality(0, "*")] = None

    @classmethod
    def get_url(cls, value: dict | BaseExtension) -> str | None:
        """Get the url of the extension"""
        if isinstance(value, dict):
            return value.get("url", None)
        if isinstance(value, BaseExtension):
            return value.url
        return None

    @classmethod
    def discriminator(cls, value: Any) -> str | None:
        url = cls.get_url(value)
        for field in fields(cls):
            for source_type in get_source_type(field.type):
                is_class = inspect.isclass(source_type)
                is_extension = is_class and issubclass(source_type, BaseExtension)
                is_not_general_extension = is_extension and not issubclass(source_type, GeneralExtension)
                if is_not_general_extension and source_type.get_url() == url:
                    return field.name
        return "other"


if __name__ == "__main__":
    pass
