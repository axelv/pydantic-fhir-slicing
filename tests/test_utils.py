from typing import Annotated, Generic, Optional, TypeVar

import pytest

from fhir_slicing.base import BaseModel
from fhir_slicing.utils import get_source_type, get_type_parameter_map, substitute_type_parameter

TValue = TypeVar("TValue")


class GenericModel(BaseModel, Generic[TValue]):
    a: TValue
    b: int


@pytest.mark.parametrize(
    "source, type_map, target",
    [
        (Optional[str], {}, (str,)),
        (list[str], {}, (str,)),
        (str, {}, (str,)),
        (list[str] | None, {}, (str,)),
        (Annotated[list[str], "some annotation"], {}, (str,)),
        (Annotated[list[str] | None, "some annotation"], {}, (str,)),
        (Annotated[list[str | int] | None, "some annotation"], {}, (str, int)),
        [TValue, {TValue: int}, (int,)],
        [list[TValue], {TValue: int}, (int,)],  # type: ignore[type]
        [GenericModel[TValue], {TValue: int}, (GenericModel[int],)],  # type: ignore[type]
    ],
)
def test_get_source_type(source, type_map, target):
    source_types = tuple(get_source_type(source, type_map=type_map))
    assert source_types == target


class Base:
    pass


class A(Base):
    pass


class B(Base):
    pass


class C:
    pass


@pytest.mark.parametrize(
    "source, expected, type_map, raises",
    [
        [A, Base, {}, None],
        [B, Base, {}, None],
        [C, Base, {}, TypeError],
        [A | None, Base, {}, None],
        [B | None, Base, {}, None],
        [C | None, Base, {}, TypeError],
        [Optional[A], Base, {}, None],
        [Optional[B], Base, {}, None],
        [Optional[C], Base, {}, TypeError],
        [list[A], Base, {}, None],
        [list[B], Base, {}, None],
        [list[C], Base, {}, TypeError],
        [list[A | B], Base, {}, None],
        [list[B | C], Base, {}, TypeError],
        [list[A | B] | None, Base, {}, None],
        [list[A | B] | None | None, Base, {}, None],
        [Annotated[list[A | B] | None, "some annotation"], Base, {}, None],
        [Annotated[list[A | C] | None, "some annotation"], Base, {}, TypeError],
        [TValue, Base, {TValue: A}, None],
        [list[TValue], Base, {TValue: B}, None],  # type: ignore[type]
    ],
)
def test_get_source_type_with_expect(source, expected, type_map, raises):
    source_types_iter = get_source_type(source, expect=expected, type_map=type_map)
    if raises:
        with pytest.raises(raises):
            tuple(source_types_iter)
    else:
        tuple(source_types_iter)


def test_type_parameter_map_with_one_parameter():
    TValue = TypeVar("TValue")

    class MyClass(Generic[TValue]):
        a: int
        b: TValue

    type_map = get_type_parameter_map(MyClass, MyClass[int])
    assert type_map == {TValue: int}


def test_type_parameter_map_with_two_parameters():
    TValue = TypeVar("TValue")
    TAnotherValue = TypeVar("TAnotherValue")

    class MyClass(Generic[TValue, TAnotherValue]):
        a: int
        b: TValue
        c: TAnotherValue

    type_map = get_type_parameter_map(MyClass, MyClass[int, str])
    assert type_map == {TValue: int, TAnotherValue: str}


TValue1 = TypeVar("TValue1")
TValue2 = TypeVar("TValue2")


@pytest.mark.parametrize(
    "generic_type, type_map, specific_type",
    [
        (list[TValue1], {TValue1: int}, list[int]),  # type: ignore[typing]
        (list[dict[str, TValue1]], {TValue1: int}, list[dict[str, int]]),  # type: ignore[typing]
        (dict[TValue1, TValue2], {TValue1: int, TValue2: str}, dict[int, str]),  # type: ignore[typing]
        (GenericModel[TValue], {TValue: int}, GenericModel[int]),  # type: ignore[typing]
    ],
)
def test_type_parameter_substitution(generic_type, type_map, specific_type):
    substituted_type = substitute_type_parameter(generic_type, type_map)
    assert substituted_type == specific_type
