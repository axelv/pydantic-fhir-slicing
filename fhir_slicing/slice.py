from functools import partial
from typing import Any, Container, Iterable, List, Literal, TypeGuard, TypeVar, overload

from fhir_slicing.typing import ElementArray

TValueType = TypeVar("TValueType", covariant=True)


class BaseSlice[TValueType]:
    def __init__(self, min_items: int = 0, max_items: int | None = None):
        self.min_items = min_items
        self.max_items = max_items

    def __repr__(self):
        return f"{self.__class__.__name__}(min_items={self.min_items}, max_items={self.max_items})"

    def __set_name__(self, owner: ElementArray[Any], name: str):
        self.slice_name = name if name != "_" else "@default"
        self.filter_elements: partial[Iterable[TValueType]] = partial(
            owner.filter_elements_for_slice, slice_name=self.slice_name
        )
        self.is_element_part_of_slice: partial[TypeGuard[TValueType]] = partial(
            owner.is_element_part_of_slice, slice_name=self.slice_name
        )


class Slice[TValueType](BaseSlice[TValueType]):
    def __get__(self, obj: ElementArray[Any], objtype: type[Container] | None = None) -> TValueType:
        try:
            return next(iter(self.filter_elements(obj)))
        except StopIteration:
            raise ValueError(f"No value for slice '{self.slice_name}'.")

    def __set__(self, obj: ElementArray[TValueType], element: Any):
        for index, old_element in enumerate(obj):
            if self.is_element_part_of_slice(old_element):
                obj[index] = element
            return
        raise ValueError("Cannot set value on slice.")


class OptionalSlice[TValueType](BaseSlice[TValueType]):
    def __get__(self, obj: ElementArray[Any], objtype: type[Container] | None = None) -> TValueType | None:
        return next(iter(self.filter_elements(obj)), None)

    def __set__(self, obj: ElementArray[Any], element: TValueType):
        for index, old_element in enumerate(obj):
            if self.is_element_part_of_slice(old_element):
                obj[index] = element
                return


class SliceList[TValueType](BaseSlice[TValueType]):
    def __get__(self, obj: ElementArray[Any], objtype: type[Container] | None = None) -> List[TValueType]:
        return [*self.filter_elements(obj)]

    def __set__(self, obj: List, value: List):
        raise NotImplementedError("Cannot set value on slice list.")


@overload
def slice(min_items: Literal[0], max_items: Literal[1]) -> OptionalSlice: ...
@overload
def slice(min_items: Literal[1], max_items: Literal[1]) -> Slice: ...
@overload
def slice(min_items: Literal[0], max_items: Literal["*"]) -> SliceList: ...
@overload
def slice(min_items: Literal[1], max_items: Literal["*"]) -> SliceList: ...
@overload
def slice(min_items: int, max_items: int | Literal["*"]) -> Any: ...
def slice(min_items: int, max_items: int | Literal["*"]):
    match (min_items, max_items):
        case (0, 1):
            return OptionalSlice(min_items=0, max_items=1)
        case (1, 1):
            return Slice(min_items=1, max_items=1)
        case (0, "*"):
            return SliceList(min_items=0)
        case (1, "*"):
            return SliceList(min_items=1)
        case (int(), "*"):
            return SliceList(min_items=min_items)
        case (int(), int()):
            return SliceList(min_items=min_items)
        case _:
            raise ValueError(f"Invalid slice specification: {min_items}..{max_items}")


def slice_validator(elements: ElementArray, *, slice_name: str, slice_descriptor: BaseSlice):
    num_items = len(list(slice_descriptor.filter_elements(elements)))
    if slice_descriptor.max_items is not None and num_items > slice_descriptor.max_items:
        raise ValueError(f"Too many items in slice '{slice_name}'")
    elif num_items < slice_descriptor.min_items:
        raise ValueError(f"Not enough items in slice '{slice_name}'")
    return elements
