from typing import Any, Literal

from pydantic import PositiveInt, TypeAdapter

from fhir_slicing import BaseModel, Slice, SliceList, slice
from fhir_slicing.extension import (
    BaseExtensionArray,
    BaseSimpleExtension,
    GeneralExtension,
)


def test_extension_model_get_url():
    class MyExtension(BaseSimpleExtension[Literal["http://example.com"], str]):
        valueString: str

    assert MyExtension.get_url() == "http://example.com"


def test_extension_array_from_extension_list():
    class MyExtensionA(BaseSimpleExtension[Literal["http://example.com/extension-a"], str]):
        valueString: str

    class MyExtensionB(BaseSimpleExtension[Literal["http://example.com/extension-b"], str]):
        valueString: str

    class ExtensionArray(BaseExtensionArray):
        a: SliceList[MyExtensionA] = slice(0, "*")
        b: Slice[MyExtensionB] = slice(1, 1)
        _: SliceList[GeneralExtension] = slice(0, "*")

    ext_list = [
        MyExtensionA(url="http://example.com/extension-a", valueString="a"),
        MyExtensionA(url="http://example.com/extension-a", valueString="a"),
        MyExtensionA(url="http://example.com/extension-a", valueString="a"),
        MyExtensionB(url="http://example.com/extension-b", valueString="b"),
        GeneralExtension.model_validate({"url": "http://example.com", "valueInteger": 3}),
    ]

    ext_array = ExtensionArray(ext_list)
    assert ext_array.a == ext_list[:3]
    assert ext_array.b == ext_list[3]
    assert list(ext_array) == ext_list


def test_extension_array_validator():
    class MyExtensionA(BaseSimpleExtension[Literal["http://example.com/extension-a"], str]):
        valueString: str

    class MyExtensionB(BaseSimpleExtension[Literal["http://example.com/extension-b"], str]):
        valueString: str

    class ExtensionArray(BaseExtensionArray):
        a: SliceList[MyExtensionA] = slice(0, "*")
        b: Slice[MyExtensionB] = slice(1, 1)
        _: SliceList[GeneralExtension] = slice(0, "*")

    ext_list = [
        {"url": "http://example.com", "valueInteger": 5},
        {"url": "http://example.com/extension-a", "valueString": "1"},
        {"url": "http://example.com/extension-a", "valueString": "2"},
        {"url": "http://example.com/extension-a", "valueString": "3"},
        {"url": "http://example.com/extension-b", "valueString": "4"},
    ]

    ext_array = TypeAdapter(ExtensionArray).validate_python(ext_list)

    assert ext_array.a == [
        MyExtensionA(url="http://example.com/extension-a", valueString="1"),
        MyExtensionA(url="http://example.com/extension-a", valueString="2"),
        MyExtensionA(url="http://example.com/extension-a", valueString="3"),
    ]

    assert ext_array.b == MyExtensionB(url="http://example.com/extension-b", valueString="4")

    ext_list_roundtrip = TypeAdapter(ExtensionArray).dump_python(ext_array, mode="python")
    assert ext_list_roundtrip == ext_list


def test_extension_array_ordering_roundtrip():
    class MyExtensionA(BaseSimpleExtension[Literal["http://example.com/extension-a"], str]):
        valueString: str

    class MyExtensionB(BaseSimpleExtension[Literal["http://example.com/extension-b"], str]):
        valueString: str

    class ExtensionArray(BaseExtensionArray):
        a: SliceList[MyExtensionA] = slice(0, "*")
        b: Slice[MyExtensionB] = slice(1, 1)

    ext_array = ExtensionArray(
        (
            MyExtensionA(url="http://example.com/extension-a", valueString="a"),
            MyExtensionA(url="http://example.com/extension-a", valueString="a"),
            MyExtensionA(url="http://example.com/extension-a", valueString="a"),
            MyExtensionB(url="http://example.com/extension-b", valueString="b"),
        )
    )

    ext_list = TypeAdapter(ExtensionArray).dump_python(ext_array)

    assert ext_list == [
        {"url": "http://example.com/extension-a", "valueString": "a"},
        {"url": "http://example.com/extension-a", "valueString": "a"},
        {"url": "http://example.com/extension-a", "valueString": "a"},
        {"url": "http://example.com/extension-b", "valueString": "b"},
    ]

    ext_array_roundtrip = TypeAdapter(ExtensionArray).validate_python(ext_list)

    assert ext_array_roundtrip == ext_array


def test_patient_use_case():
    class MultipleBirth(
        BaseSimpleExtension[Literal["http://hl7.org/fhir/StructureDefinition/patient-multipleBirth"], PositiveInt]
    ):
        valueInteger: PositiveInt

    class PatientExtensions(BaseExtensionArray):
        multiple_birth: Slice[MultipleBirth] = slice(1, 1)

    class PatientName(BaseModel):
        text: str
        given: list[str] | None = None
        family: str | None = None
        use: Literal["usual", "official", "temp", "nickname", "anounymous", "old", "maiden"] | None = None

    class Patient(BaseModel):
        extensions: PatientExtensions
        resourceType: Literal["Patient"] = "Patient"
        name: list[PatientName] | None = None

        @property
        def multiple_birth(self):
            return self.extensions.multiple_birth.valueInteger

        @multiple_birth.setter
        def set_multiple_birth(self, value: PositiveInt):
            self.extensions.multiple_birth.valueInteger = value

    patient = Patient.model_validate(
        {
            "resourceType": "Patient",
            "name": [
                {
                    "text": "John Doe",
                    "given": ["John"],
                    "family": "Doe",
                    "use": "official",
                },
            ],
            "extensions": [
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/patient-multipleBirth",
                    "valueInteger": 3,
                }
            ],
        }
    )

    assert patient.extensions.multiple_birth.valueInteger == 3
    assert patient.multiple_birth == 3


def test_blood_pressure_use_case():
    class Quantity(BaseModel):
        value: float
        unit: str

    class Coding(BaseModel):
        system: str
        code: str
        display: str

    class CodeableConcept(BaseModel):
        coding: list[Coding]
        text: str | None = None

    class BloodPressureComponent(BaseModel):
        valueQuantity: Quantity
        code: CodeableConcept

    class BloodPressureComponents(BaseExtensionArray):
        systolic: Slice[BloodPressureComponent] = slice(1, 1)
        diastolic: Slice[BloodPressureComponent] = slice(1, 1)

        @classmethod
        def discriminator(cls, value: Any) -> str:
            code = value.get("code", {}).get("coding", [{}])[0].get("code", None)
            match code:
                case "8480-6":
                    return "systolic"
                case "8462-4":
                    return "diastolic"
                case _:
                    return "@default"

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
