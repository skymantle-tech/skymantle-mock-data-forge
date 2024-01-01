from typing import TypedDict


class DynamoDbStackConfig(TypedDict):
    name: str
    output: str


class DynamoDbTableConfig(TypedDict):
    name: str
    ssm: str
    stack: DynamoDbStackConfig


class DynamoDbForgeConfig(TypedDict):
    table: DynamoDbTableConfig
    primary_key_names: list[str]
    items: list[dict]


class DataForgeConfig(TypedDict):
    forge_id: str
    dynamodb: DynamoDbForgeConfig
