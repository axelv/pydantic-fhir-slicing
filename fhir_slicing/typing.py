from typing import Annotated, Iterable, List, Optional, Self, TypeGuard, TypeVar

from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema


def is_null_schema(schema: JsonSchemaValue) -> bool:
    return "type" in schema and schema["type"] == "null"


class NotNullable:
    @classmethod
    def __get_pydantic_json_schema__(
        cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(core_schema)
        assert "anyOf" in json_schema
        not_null_schema = next(
            (schema for schema in filter(lambda x: not is_null_schema(x), json_schema["anyOf"])), None
        )
        assert not_null_schema is not None
        return not_null_schema


T = TypeVar("T")
Omissible = Annotated[Optional[T], NotNullable()]


class ElementArray[TElement](List[TElement]):
    @classmethod
    def filter_elements_for_slice(cls, elements: Self, slice_name: str) -> Iterable[TElement]:
        """Get the slice name for a given element."""
        ...

    @classmethod
    def is_element_part_of_slice(cls, element: TElement, slice_name: str) -> TypeGuard[TElement]:
        """Check if an element is part of a slice."""
        ...
