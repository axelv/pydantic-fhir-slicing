from typing import Annotated, Literal

from pydantic import AfterValidator

from fhir_slicing import Slice, SliceList, slice
from fhir_slicing.base import BaseModel
from fhir_slicing.coding import GeneralCoding, LOINCCoding
from fhir_slicing.element_array import BaseElementArray


def test_blood_pressure_use_case():
    class Quantity(BaseModel):
        value: float
        unit: str

    class CodingArray(BaseElementArray[LOINCCoding | GeneralCoding]):
        loinc: Slice[LOINCCoding] = slice(1, 1)
        _: SliceList[GeneralCoding] = slice(0, "*")

    class CodeableConcept(BaseModel):
        coding: CodingArray
        text: str | None = None

    def is_systolic(value: CodeableConcept):
        if value.coding.loinc.code != "8480-6":
            raise ValueError("Not a systolic blood pressure")
        return value

    def is_diastolic(value: CodeableConcept):
        if value.coding.loinc.code != "8462-4":
            raise ValueError("Not a diastolic blood pressure")
        return value

    class SystolicPressureComponent(BaseModel):
        valueQuantity: Quantity
        code: Annotated[CodeableConcept, AfterValidator(is_systolic)]

    class DiastolicPressureComponent(BaseModel):
        valueQuantity: Quantity
        code: Annotated[CodeableConcept, AfterValidator(is_diastolic)]

    class BloodPressureComponents(BaseElementArray):
        systolic: Slice[SystolicPressureComponent] = slice(1, 1)
        diastolic: Slice[DiastolicPressureComponent] = slice(1, 1)

    class BloodPressure(BaseModel):
        resourceType: Literal["Observation"] = "Observation"
        code: CodeableConcept
        components: BloodPressureComponents

        @property
        def systolic(self):
            return self.components.systolic.valueQuantity.value

        @property
        def diastolic(self):
            return self.components.diastolic.valueQuantity.value

    blood_pressure = BloodPressure.model_validate(
        {
            "resourceType": "Observation",
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "55284-4",
                        "display": "Blood pressure",
                    }
                ],
                "text": "Blood pressure",
            },
            "components": [
                {
                    "valueQuantity": {"value": 120, "unit": "mm[Hg]"},
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "8480-6",
                                "display": "Systolic blood pressure",
                            }
                        ],
                        "text": "Systolic blood pressure",
                    },
                },
                {
                    "valueQuantity": {"value": 80, "unit": "mm[Hg]"},
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "8462-4",
                                "display": "Diastolic blood pressure",
                            }
                        ],
                        "text": "Diastolic blood pressure",
                    },
                },
            ],
        }
    )

    assert blood_pressure.components.systolic.valueQuantity.value == 120
    assert blood_pressure.systolic == 120
    assert blood_pressure.components.diastolic.valueQuantity.value == 80
    assert blood_pressure.diastolic == 80
