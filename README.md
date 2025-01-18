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

This library introduces a more intuitive way to access FHIR data using named slices, inspired by FHIR's slicing mechanism:

```python
from pydantic_fhir_slicing import ElementArray
from typing import Any, Annotated

class Component(BaseModel):
    code: CodeableConcept
    valueQuantity: Quantity

class BPComponents(ElementArray[Component]):
    systolic: Annotated[Systolic, Cardinality(1, 1)] = Slice()
    diastolic: Annotated[Diastolic, Cardinality(1, 1)] = Slice()

    def discriminator(self, item: Component) -> str:
        return item.code.coding[0].code

class BloodPressureObservation(Resource):
    component: BPComponents

# Access components naturally
bp = BloodPressureObservation.model_validate(data)
systolic = bp.component.systolic.valueQuantity.value
diastolic = bp.component.diastolic.valueQuantity.value
```

## Handling Partial Knowledge

FHIR resources often include extensions where only some values are known ahead of time. Our library handles this gracefully:

```python
class PatientExtensions(SliceableList[Extension]):
    birthPlace: Annotated[Extension, Cardinality(0, 1)] = Slice()

    def discriminator(self, item: Any) -> str:
        return item.url

class Patient(Resource):
    extension: PatientExtensions

# Access known extensions by name, while preserving access to unknown ones
patient.extension.birthPlace.valueAddress.city
patient.extension[0]  # Still works for accessing any extension
```

## Installation

```bash
pip install fhir-pydantic-slicing
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License
