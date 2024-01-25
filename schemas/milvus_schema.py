from pymilvus import CollectionSchema, FieldSchema, DataType

fields = [
    FieldSchema(
        name="id",
        dtype=DataType.VARCHAR,
        max_length=32,
        is_primary=True,
    ),
    FieldSchema(
        name="text",
        dtype=DataType.VARCHAR,
        max_length=526,
        default_value=""
    ),
    FieldSchema(
        name="ns",
        dtype=DataType.VARCHAR,
        max_length=32,
        default_value="default"
    ),
    FieldSchema(
        name="embedding",
        dtype=DataType.FLOAT_VECTOR,
        dim=1536
    )
]

Schema = CollectionSchema(
    fields=fields,
    description="Knowledge search",
    enable_dynamic_field=True,
)
