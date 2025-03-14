from .base import BaseModel
from .coding import BaseCoding


class UsageCoding[TSystem: str, TCode: str, TVersion: str | None](BaseCoding[TSystem]):
    code: TCode
    version: TVersion | None = None

    def __eq__(self, other: object):
        if not isinstance(other, UsageCoding):
            return False
        return hash((self.system, self.code, self.version)) == hash((other.system, other.code, other.version))


class BaseUsageContext[TUsageCoding: UsageCoding](BaseModel):
    code: TUsageCoding
    model_config = {"extra": "allow"}
