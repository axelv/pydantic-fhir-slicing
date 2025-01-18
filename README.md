# FHIR-Pydantic Slicing

A Python library that simplifies working with FHIR resources using Pydantic models and smart slicing.

## The Challenge

Working with FHIR resources in Python can be challenging due to their complex structure and extensibility. FHIR resources often contain:
- Arrays of nested objects
- Optional extensions
- Variable cardinality (0..*, 1..*, 0..1, etc.)

This leads to verbose and error-prone code when accessing nested data:

```python
# Traditional way to access systolic blood pressure
bp_reading = observation.component[0].valueQuantity.value  # Fragile!

# or with type checking
systolic = next(
    (c.valueQuantity.value
     for c in observation.component
     if c.code.coding[0].code == "8480-6"),
    None
)
```

## Solution: Smart Slicing

This library introduces a more intuitive way to access FHIR data using named slices, inspired by FHIR's slicing mechanism.

Known slices are defined as annotated fields in Pydantic models, which provide:
- Validation of slice cardinality
- Type safety for slice elements
- Improved readability

Unkown elements are left untouched and the order of elements is preserved.

**Example: Patient with birthPlace extension**

```python
from typing import Any, Annotated
from pydantic_fhir_slicing import Slice, ElementArray
from my_fhir_types import Address, BaseModel

class AddressExtension(BaseModel):
    url: str
    valueAddress: Address

class PatientExtensions(ElementArray):
    birthPlace: Annotated[AddressExtension] = Slice(1, 1)

    def discriminator(self, item: Any) -> str:
        url = item.get("url", None)
        match url
            case "http://hl7.org/fhir/StructureDefinition/patient-birthPlace":
                return "birthPlace"
            case _:
                return "@default"

class Patient(BaseModel):
    extension: PatientExtensions

# Access known extensions by name, while preserving access to unknown ones
patient.extension.birthPlace.valueAddress.city
patient.extension[0]  # Still works for accessing any extension

```

**Example: Blood Pressure Observation with systolic and diastolic components**

```python
from pydantic_fhir_slicing import ElementArray
from typing import Any, Annotated
from my_fhir_types import CodeableConcept, Quantity, BaseModel

class QuantityComponent(BaseModel):
    code: CodeableConcept
    valueQuantity: Quantity

class BPComponents(ElementArray):
    systolic: QuantityComponent = Slice(1, 1)
    diastolic: QuantityComponent = Slice(1, 1)

    def discriminator(self, item: Component) -> str:
        try:
            code = item["code"]["coding"][0]["code"]
            match code
                case "8480-6":
                    return "systolic"
                case "8462-4":
                    return "diastolic"
                case _:
                    return "@default"
        except (KeyError, IndexError):
            return "@default"

class BloodPressureObservation(BaseModel):
    code: CodeableConcept
    component: BPComponents

# Access components naturally
bp = BloodPressureObservation.model_validate(data)
systolic = bp.component.systolic.valueQuantity.value
diastolic = bp.component.diastolic.valueQuantity.value

```

## Installation

```bash
pip install pydantic-fhir-slicing
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License
