from pymilvus import CollectionSchema, FieldSchema, DataType

id = FieldSchema(
    name="id",
    dtype=DataType.VARCHAR,
    max_length=32,
    is_primary=True,
)
text = FieldSchema(
    name="text",
    dtype=DataType.VARCHAR,
    max_length=4000,
    default_value=""
)
embedding = FieldSchema(
    name="embedding",
    dtype=DataType.FLOAT_VECTOR,
    dim=1536
)
Schema = CollectionSchema(
    fields=[id, text, embedding],
    description="Knowledge search",
    enable_dynamic_field=True,
)
