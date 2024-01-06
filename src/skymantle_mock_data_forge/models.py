from enum import Enum
from typing import TypedDict


class CfnStackConfig(TypedDict):
    name: str
    output: str


class ResourceConfig(TypedDict):
    name: str
    ssm: str
    stack: CfnStackConfig


class DynamoDbForgeConfig(TypedDict):
    table: ResourceConfig
    primary_key_names: list[str]
    items: list[dict]


class S3ObjectDataConfig(TypedDict):
    text: str
    json: dict | list[dict]
    base64: str
    csv: list[list[str | int]]


class S3ObjectConfig(TypedDict):
    key: str
    data: S3ObjectDataConfig


class S3ForgeConfig(TypedDict):
    bucket: ResourceConfig
    s3_objects: list[S3ObjectConfig]


class DataForgeConfig(TypedDict):
    forge_id: str
    dynamodb: DynamoDbForgeConfig
    s3: S3ForgeConfig


class OverideType(Enum):
    REPLACE_VALUE = 0
    FORMAT_VALUE = 1
    CALL_FUNCTION = 2


class DataForgeConfigOverride(TypedDict):
    forge_id: str | None
    key_paths: str | list[str]
    override_type: OverideType
    override: any
