import inspect
from functools import partial
from typing import (
    Any,
    ClassVar,
    Iterable,
    Literal,
    LiteralString,
    Self,
    TypeGuard,
    TypeVar,
    get_origin,
)

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from fhir_slicing.slice import BaseSlice, slice_validator
from fhir_slicing.slice_schema import get_slice_union_schema
from fhir_slicing.typing import ElementArray

from .utils import FHIRType, get_source_type, get_type_parameter_map

TUrl = TypeVar("TUrl", bound=LiteralString)
TFhirType = TypeVar("TFhirType", bound=FHIRType)
TPythonType = TypeVar("TPythonType")


# resource.extension["itemControl"].valueCodeableConcept.coding["tiro"].code

DiscriminatorType = Literal["value", "exists", "type"]
TDefaultElement = TypeVar("TDefaultElement")

FIELD_NAME_TO_SLICE_NAME = {"_": "@default"}


def get_all_parent_classes(cls):
    return inspect.getmro(cls)


def get_slice_annotations(element_array_cls: type[Any]) -> dict[str, type]:
    return {
        FIELD_NAME_TO_SLICE_NAME.get(field_name, field_name): annotation
        for cls in get_all_parent_classes(element_array_cls)
        for field_name, annotation in inspect.get_annotations(cls).items()
        if get_origin(annotation) is not ClassVar
    }


class BaseElementArray[TElement](ElementArray[TElement]):
    """A collection of elements that can be sliced and named using a discriminator."""

    @classmethod
    def filter_elements_for_slice(cls, elements: Self, slice_name: str) -> Iterable[TElement]:
        """Get the slice name for a given element."""
        for element in elements:
            if cls.is_element_part_of_slice(element, slice_name):
                yield element

    @classmethod
    def is_element_part_of_slice(cls, element: TElement, slice_name: str) -> TypeGuard[TElement]:
        """Check if an element is part of a slice."""
        annotation = get_slice_annotations(cls)[slice_name]
        for element_type in get_source_type(annotation, type_map={}):
            if isinstance(element, element_type):
                return True
        return False

    @classmethod
    def get_validators(cls):
        def get_slice_validator(cls, slice_name):
            descriptor = inspect.getattr_static(cls, slice_name)
            if not isinstance(descriptor, BaseSlice):
                raise TypeError(f"Expected Slice, OptionalSlice or SliceList, got {type(descriptor)}")

        for field_name in inspect.get_annotations(cls).keys():
            descriptor = inspect.getattr_static(cls, field_name)
            if not isinstance(descriptor, BaseSlice):
                raise TypeError(f"Expected Slice, OptionalSlice or SliceList, got {type(descriptor)}")
            slice_name = FIELD_NAME_TO_SLICE_NAME.get(field_name, field_name)
            yield partial(slice_validator, slice_name=slice_name, slice_descriptor=descriptor)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler):
        """Get the Pydantic core schema for the element array."""

        type_map = get_type_parameter_map(cls, source_type)
        slice_union_schema = get_slice_union_schema(
            get_slice_annotations(source_type), handler=handler, type_map=type_map
        )
        list_schema = core_schema.list_schema(slice_union_schema)
        # TODO add after validators for cardinality of each slice

        schema = list_schema
        for validator in cls.get_validators():
            schema = core_schema.no_info_after_validator_function(
                validator,
                schema,
            )
        return core_schema.json_or_python_schema(
            core_schema.no_info_after_validator_function(
                cls,
                schema,
            ),
            core_schema.union_schema(
                [
                    core_schema.is_instance_schema(cls),
                    core_schema.no_info_after_validator_function(cls, schema),
                ]
            ),
        )


if __name__ == "__main__":
    pass
