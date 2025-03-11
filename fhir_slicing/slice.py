from functools import partial
from typing import Annotated, Any, Container, Iterable, List, Literal, TypeGuard, TypeVar, overload

import annotated_types

from fhir_slicing.typing import ElementArray

TValueType = TypeVar("TValueType", covariant=True)


class BaseSlice[TValueType]:
    def __init__(self, min_items: int = 0, max_items: int | Literal["*"] = "*"):
        self.min_items = min_items
        self.max_items = max_items

    def __set_name__(self, owner: ElementArray[Any], name: str):
        self.name = name
        self.filter_elements: partial[Iterable[TValueType]] = partial(
            owner.filter_elements_for_slice, slice_name=self.name
        )
        self.is_element_part_of_slice: partial[TypeGuard[TValueType]] = partial(
            owner.is_element_part_of_slice, slice_name=self.name
        )


class Slice[TValueType](BaseSlice[TValueType]):
    def __get__(self, obj: ElementArray[Any], objtype: type[Container] | None = None) -> TValueType:
        try:
            return next(iter(self.filter_elements(obj)))
        except StopIteration:
            raise ValueError(f"No value for slice '{self.name}'.")

    def __set__(self, obj: ElementArray[TValueType], element: Any):
        for index, old_element in enumerate(obj):
            if self.is_element_part_of_slice(old_element):
                obj[index] = element
            return
        raise ValueError("Cannot set value on slice.")


class OptionalSlice[TValueType](BaseSlice[TValueType]):
    def __set_name__(self, owner: ElementArray[Any], name: str):
        self.name = name
        self.filter_elements: partial[Iterable[TValueType]] = partial(
            owner.filter_elements_for_slice, slice_name=self.name
        )
        self.is_element_part_of_slice: partial[TypeGuard[TValueType]] = partial(
            owner.is_element_part_of_slice, slice_name=self.name
        )

    def __get__(self, obj: ElementArray[Any], objtype: type[Container] | None = None) -> TValueType | None:
        return next(iter(self.filter_elements(obj)), None)

    def __set__(self, obj: ElementArray[Any], element: TValueType):
        for index, old_element in enumerate(obj):
            if self.is_element_part_of_slice(old_element):
                obj[index] = element
                return


class SliceList[TValueType](BaseSlice[TValueType]):
    def __set_name__(self, owner: ElementArray[Any], name: str):
        self.name = name
        self.filter_elements: partial[Iterable[TValueType]] = partial(
            owner.filter_elements_for_slice, slice_name=self.name
        )
        self.is_element_part_of_slice: partial[TypeGuard[TValueType]] = partial(
            owner.is_element_part_of_slice, slice_name=self.name
        )

    def __get__(self, obj: ElementArray[Any], objtype: type[Container] | None = None) -> List[TValueType]:
        return [*self.filter_elements(obj)]

    def __set__(self, obj: List, value: List):
        raise NotImplementedError("Cannot set value on slice list.")


NonZeroPositiveInt = Annotated[int, annotated_types.Gt(0)]


@overload
def slice(min: Literal[0], max: Literal[1]) -> OptionalSlice: ...
@overload
def slice(min: Literal[1], max: Literal[1]) -> Slice: ...
@overload
def slice(min: NonZeroPositiveInt, max: Literal["*"]) -> SliceList: ...
def slice(min: int, max: int | Literal["*"]):
    match (min, max):
        case (0, 1):
            return OptionalSlice(min_items=0, max_items=1)
        case (1, 1):
            return Slice(min_items=1, max_items=1)
        case (0, "*"):
            return SliceList(min_items=0, max_items="*")
        case (1, "*"):
            return SliceList(min_items=0, max_items="*")
        case _:
            raise ValueError("Invalid slice cardinality.")
