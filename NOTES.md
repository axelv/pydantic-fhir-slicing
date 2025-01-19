## FHIR Slicing for more intuitive data access

FHIR slicing is a powerful mechanism to structure arrays of nested objects in FHIR resources. Given the 80/20 rule, FHIR naturally has lots of elements with cardinality `0..*` or `1..*`to allow for extensibility. But in specific cases, it is possible to constrain parts of these arrays and sometimes give names to certain elements.
Therefore, the standard has introduced the concept of slicing. Slicing was originally meant to be used in the context of profiles. In this post, we will explore how slicing can make our Python code more intuitive and less error-prone.

## Example: [Blood Pressure Observation][1]

Let's consider a simplified example based on the Blood Pressure Profile. This resource has a component array with systolic and diastolic blood pressure measurements. We can define a Pydantic model for this resource as follows:

```python
from pydantic import BaseModel

class Component(BaseModel):
    code: CodeableConcept
    valueQuantity: Quantity
    valueCodeableConcept: CodeableConcept
    valueString: str
    valueBoolean: bool
    valueRange: Range
    valueRatio: Ratio
    # and many more types for value[x]

class BloodPressureObservation(BaseModel):
    resourceType: Literal['Observation']
    code: CodeableConcept
    component: List[Component]


# Access components naturally
bp = BloodPressureObservation.model_validate(data)
systolic = next(
    (c.valueQuantity.value
     for c in bp.component
     if c.code.coding[0].code == "8480-6"),
    None
)
diastolic = next(
    (c.valueQuantity.value
     for c in bp.component
     if c.code.coding[0].code == "8462-4"),
    None
)

```
**Note**: The code above is a simplified version of the Blood Pressure Observation. The actual resource has more fields and complexity. Furthermore, some of the simpler models are left out for brevity.

Problems with this approach:

1. **Readability**: The code is verbose and hard to read. It's not immediately clear what the code is doing.
2. **Validation**: The code doesn't provide any validation for the slices. There is no guarantee that systolic and diastolic components are present in the observation.
3. **Type Safety**: The code doesn't provide any type safety for the slices. There is no guarantee that the component has a valueQuantity element.


## Validating slices using Pydantic

The Pydantic equivalent of slice elements is [tagged unions][2]. So following the best practices of Pydantic, we can define a custom type for sliceable element arrays. The only requirement is that a method `__get_pydantic_core_schema__` is implemented.


So let's start with a first rudimentary implementation of a sliceable array:

```python

class ElementArray(List):

    @classmethod
    def discriminator(cls, item: Any) -> str:
        raise NotImplementedError

    @classmethod
    def get_schema_for_slices(cls, handler: GetCoreSchemaHandler)->dict[str, CoreSchema]:
        raise NotImplementedError

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> Any:

        # Get the schema for the slices
        choices: dict[str, CoreSchema] = cls.get_schema_for_slices(handler)
        # Create a tagged union schema wrapped in a list schema
        schema = core_schema.list_schema(core_schema.tagged_union_schema(choices=choices, discriminator=cls.discriminator))
        # Return the schema
        return core_schema.no_info_after_validator_function(cls, schema)

```

This is a first implementation of a sliceable array. The `get_schema_for_slices` method should return a dictionary with the slice names as keys and their schema as values. The `discriminator` method should return a string that is used to determine which slice to use.

Now we need to specify the names and expected types of the slices somewhere. Inspired by how Python dataclasses work, we can use attributes with type annotations to specify the slices.

```python

class ElementArray(List):

    @classmethod
    @abstractmethod
    def discriminator(self, item: Any) -> str:
        """Get the slice name for a given value.

        This method must be implemented by the subclass.
        """
        ...

    @classmethod
    def get_schema_for_slices(self, handler: GetCoreSchemaHandler)->dict[str, CoreSchema]:
        """Generate a schema for each slice.

        Args:
            handler (GetCoreSchemaHandler): The handler to generate the schema

        Returns:
            dict[str, CoreSchema]: The name of the slice and the schema
        """
        return {
            slice_name: handler(slice_type)
            for slice_name, slice_type in inspect.get_annotations(self)
        }

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> Any:
        # Get the schema for the slices
        choices: dict[str, CoreSchema] = cls.get_schema_for_slices(handler)
        # Create a tagged union schema wrapped in a list schema
        schema = core_schema.list_schema(core_schema.tagged_union_schema(choices=choices, discriminator=cls.discriminator))
        # Return the schema
        return core_schema.no_info_after_validator_function(cls, schema)

```

Now we can define a sliceable array for the components of the Blood Pressure Observation:

```python

class QuantityComponent(BaseModel):
    code: CodeableConcept
    valueQuantity: Quantity

class BPComponents(ElementArray):

    systolic: QuantityComponent
    diastolic: QuantityComponent

    @classmethod
    def discriminator(cls, item: Component) -> str:
        match item.code.coding[0].code:
            case "8480-6":
                return "systolic"
            case "8462-4":
                return "diastolic"
            case _:
                raise ValueError(f"Unknown code {item.code.coding[0].code}")

bp = BloodPressureObservation.model_validate(data) # ✅ validation of the slices

```

With the above adaptations we have solved the validation part of the problem. But we still have a list of components and no way to reliably access them except by using a loop and checking the code.

## Accessing slices using the Descriptor Protocol

Python has powerful features to modify the behavior of objects. One of these features is the Descriptor protocol. This protocol allows us to define custom behavior for attribute access. We can use this to create a more intuitive way to access slices.

```python

class Slice:
    """A descriptor to access a slice of a list."""

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        # Get the slice name
        return next(
            (c
             for c in instance
             if owner.discriminator(c) == self.name),
            None
        )

    def __set_name__(self, owner, name):
        # Store the slice name
        self.name = name

```

Now we can use the `Slice` descriptor to access the slices of the components:

```python

class QuantityComponent(BaseModel):
    code: CodeableConcept
    valueQuantity: Quantity

class BPComponents(ElementArray):

    systolic: QuantityComponent = Slice()
    diastolic: QuantityComponent = Slice()

    @classmethod
    def discriminator(cls, item: Component) -> str:
        match item.code.coding[0].code:
            case "8480-6":
                return "systolic"
            case "8462-4":
                return "diastolic"
            case _:
                raise ValueError(f"Unknown code {item.code.coding[0].code}")

class BloodPressureObservation(BaseModel):
    resourceType: Literal['Observation']
    code: CodeableConcept
    component: BPComponents

bp = BloodPressureObservation.model_validate(data)
systolic = bp.component.systolic.valueQuantity.value # ✅ type safety

```

## Shortcomings in the current implementation:

1. **Cardinality**: slices are not taking into account cardinality. The cardinality also affects the type annotation of the slice:
    - `0..1`: `Optional[Element]`
    - `0..*`: `List[Element]`
    - `1..*`: `List[Element]`

2. **Default slices**: the slices are not taking into account the default slices.

3. **Mutability**: the current implementation is not mutable. It is not possible to alter the slices of the list.


These shortcomings have been addressed in the final implementation of the library. The final implementation can be found in the [pydantic-fhir-slicing](http://github.com/axelv/pydantic-fhir-slicing) repository.


[1]: https://www.hl7.org/fhir/bp.html "Blood Pressure Observation"
[2]: https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions "Pydantic Discriminated Unions"
