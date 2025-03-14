from typing import Literal

from pydantic import BaseModel

from fhir_slicing import OptionalSlice, SliceList, slice
from fhir_slicing.element_array import BaseElementArray
from fhir_slicing.usage_context import BaseUsageContext, UsageCoding

UsageContextType = Literal["http://terminology.hl7.org/CodeSystem/usage-context-type"]
AgeContextCoding = UsageCoding[UsageContextType, Literal["age"], None]
ProgramContextCoding = UsageCoding[UsageContextType, Literal["program"], None]


class Age(BaseModel):
    value: int
    system: Literal["http://unitsofmeasure.org"] = "http://unitsofmeasure.org"
    code: Literal["a"] = "a"
    unit: Literal["year"] = "year"


class AgeRange(BaseModel):
    low: Age
    high: Age


class AgeContext(BaseUsageContext[AgeContextCoding]):
    valueRange: AgeRange

    @classmethod
    def from_age_range(cls, low: int, high: int):
        return cls(
            valueRange=AgeRange(low=Age(value=low), high=Age(value=high)),
            code=AgeContextCoding(system="http://terminology.hl7.org/CodeSystem/usage-context-type", code="age"),
        )


class Reference(BaseModel):
    reference: str


class ProjectContext(BaseUsageContext[ProgramContextCoding]):
    valueReference: Reference

    @classmethod
    def from_reference(cls, reference: str):
        return cls(
            valueReference=Reference(reference=reference),
            code=ProgramContextCoding(
                system="http://terminology.hl7.org/CodeSystem/usage-context-type", code="program"
            ),
        )


def test_usage_context_array_from_usage_context_list():
    class UsageContextArray(BaseElementArray):
        project: SliceList[ProjectContext] = slice(0, "*")
        age_range: OptionalSlice[AgeContext] = slice(0, 1)
        _: SliceList[BaseUsageContext] = slice(0, "*")

    ctx_list = [
        ProjectContext.from_reference("https://example.com/project1"),
        AgeContext.from_age_range(18, 65),
        ProjectContext.from_reference("https://example.com/project2"),
        BaseUsageContext.model_validate(
            {
                "valueCodeableConcept": {
                    "coding": [{"system": "http://snomed.info/sct", "code": "123456789", "display": "test"}],
                },
                "code": {
                    "system": "http://terminology.hl7.org/CodeSystem/usage-context-type",
                    "code": "gender",
                    "display": "Gender",
                },
            }
        ),
    ]

    ctx_array = UsageContextArray(ctx_list)
    assert ctx_array.project == [ctx_list[0], ctx_list[2]]
    assert ctx_array.age_range == ctx_list[1]
    assert list(ctx_array) == ctx_list
