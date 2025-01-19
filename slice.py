from typing import Any, Container, Iterable, List, Literal

from element_array import BaseElementArray


class Slice:
    def __init__(self, min: int, max: int | Literal["*"]):
        self.min = min
        self.max = max

    def __set_name__(self, owner: BaseElementArray, name):
        self.name = name
        self.discriminator_func = owner.discriminator

    def filter_element(self, element):
        return self.discriminator_func(element) == self.name

    def __get__(self, obj: Iterable, objtype: type[Container] | None = None):
        match (self.min, self.max):
            case 0, 1:
                return next(iter(filter(self.filter_element, obj)), None)
            case 1, 1:
                return next(iter(filter(self.filter_element, obj)))
            case _:
                return [*filter(self.filter_element, obj)]

    def __set__(self, obj: List, value: Any):
        match (self.min, self.max):
            case 0, 1:
                for index, element in enumerate(obj):
                    if self.discriminator_func(element) == self.discriminator_func(value):
                        obj[index] = value
                        return
                obj.append(value)
            case 1, 1:
                obj.clear()
                obj.append(value)
            case _:
                raise NotImplementedError("Cannot set value on slice with cardinality > 1")
