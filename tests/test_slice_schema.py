from typing import TypeVar

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

from fhir_slicing.slice import OptionalSlice, Slice, SliceList
from fhir_slicing.slice_schema import get_slice_union_schema


class DummySchemaHandler(GetCoreSchemaHandler):
    def __call__(self, source_type: type):
        return self.generate_schema(source_type)

    def generate_schema(self, source_type: type):
        if source_type is int:
            return core_schema.int_schema()
        elif source_type is str:
            return core_schema.str_schema()
        elif source_type is list[str]:
            return core_schema.list_schema(core_schema.str_schema())
        raise ValueError(f"Unsupported type: {source_type}")


def test_slices_schema():
    slice_annotations = {"a": Slice[int], "b": OptionalSlice[str | None], "@default": SliceList[list[str]]}
    type_map = {}

    schema = get_slice_union_schema(slice_annotations, handler=DummySchemaHandler(), type_map=type_map)

    assert schema == core_schema.union_schema(
        [
            core_schema.union_schema(
                [
                    (core_schema.int_schema(), "a"),
                    (core_schema.str_schema(), "b"),
                ],
                mode="smart",
            ),
            core_schema.str_schema(),
        ],
        mode="left_to_right",
    )


def test_slices_schema_with_type_vars():
    TValue = TypeVar("TValue")
    slice_annotations = {"a": Slice[TValue], "b": OptionalSlice[str | None], "@default": SliceList[list[str]]}  # type: ignore[typing]
    type_map = {TValue: int}

    schema = get_slice_union_schema(slice_annotations, handler=DummySchemaHandler(), type_map=type_map)

    assert schema == core_schema.union_schema(
        [
            core_schema.union_schema(
                [
                    (core_schema.int_schema(), "a"),
                    (core_schema.str_schema(), "b"),
                ],
                mode="smart",
            ),
            core_schema.str_schema(),
        ],
        mode="left_to_right",
    )
