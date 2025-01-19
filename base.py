from collections.abc import Mapping
from typing import Iterable

import pydantic as pd


class BaseModel(pd.BaseModel, Mapping):
    def __iter__(self) -> Iterable[str]:  # type: ignore[override]
        return iter([field_name for field_name in self.model_fields_set])

    def __len__(self):
        return len(self.model_fields)

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)
