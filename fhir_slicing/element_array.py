import inspect
from typing import (
    Any,
    ClassVar,
    Iterable,
    Literal,
    LiteralString,
    Self,
    TypeVar,
    get_origin,
)

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from fhir_slicing.slice_schema import get_slice_union_schema
from fhir_slicing.typing import ElementArray

from .utils import FHIRType, get_source_type

TUrl = TypeVar("TUrl", bound=LiteralString)
TFhirType = TypeVar("TFhirType", bound=FHIRType)
TPythonType = TypeVar("TPythonType")


# resource.extension["itemControl"].valueCodeableConcept.coding["tiro"].code

DiscriminatorType = Literal["value", "exists", "type"]
TDefaultElement = TypeVar("TDefaultElement")

FIELD_NAME_TO_SLICE_NAME = {"_": "@default"}


def get_slice_annotations(cls) -> dict[str, type]:
    return {
        FIELD_NAME_TO_SLICE_NAME.get(field_name, field_name): annotation
        for field_name, annotation in inspect.get_annotations(cls).items()
        if get_origin(annotation) is not ClassVar
    }


class BaseElementArray[TDefaultElement](ElementArray[TDefaultElement]):
    """A collection of elements that can be sliced and named using a discriminator."""

    @classmethod
    def filter_elements_for_slice(cls, elements: Self, slice_name: str) -> Iterable[TDefaultElement]:
        """Get the slice name for a given element."""
        for element in elements:
            if cls.is_element_part_of_slice(element, slice_name):
                yield element

    @classmethod
    def is_element_part_of_slice(cls, element: TDefaultElement, slice_name: str) -> bool:
        """Check if an element is part of a slice."""
        annotation = get_slice_annotations(cls)[slice_name]
        for element_type in get_source_type(annotation):
            if isinstance(element, element_type):
                return True
        return False

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler):
        """Get the Pydantic core schema for the element array."""
        slice_union_schema = get_slice_union_schema(source_type, handler, slice_annotations=get_slice_annotations(cls))
        list_schema = core_schema.list_schema(slice_union_schema)
        # TODO add after validators for cardinality of each slice
        return core_schema.json_or_python_schema(
            core_schema.no_info_after_validator_function(
                cls,
                list_schema,
            ),
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(cls),
                    core_schema.no_info_after_validator_function(cls, list_schema),
                ]
            ),
        )


if __name__ == "__main__":
    pass
