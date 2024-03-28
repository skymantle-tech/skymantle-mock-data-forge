from enum import Enum
from typing import Any, TypedDict


class ForgeQuery(TypedDict):
    StringEquals: dict[str, str | list[str]]
    StringLike: dict[str, str | list[str]]


class CfnStackConfig(TypedDict):
    name: str
    output: str


class ResourceConfig(TypedDict):
    name: str
    ssm: str
    stack: CfnStackConfig


class DynamoDbItemConfig(TypedDict):
    tags: dict[str, str | list[str]]
    data: dict


class DynamoDbForgeConfig(TypedDict):
    table: ResourceConfig
    primary_key_names: list[str]
    items: list[DynamoDbItemConfig]


class S3ObjectDataConfig(TypedDict):
    text: str
    json: dict | list[dict]
    base64: str
    csv: list[list[str | int]]
    file: str


class S3ObjectConfig(TypedDict):
    key: str
    tags: dict[str, str | list[str]]
    data: S3ObjectDataConfig


class S3ForgeConfig(TypedDict):
    bucket: ResourceConfig
    s3_objects: list[S3ObjectConfig]


class DataForgeConfig(TypedDict):
    forge_id: str
    dynamodb: DynamoDbForgeConfig
    s3: S3ForgeConfig


class OverrideType(Enum):
    REPLACE_VALUE = 0
    FORMAT_VALUE = 1
    CALL_FUNCTION = 2


class DataForgeConfigOverride(TypedDict):
    forge_id: str | None
    key_paths: str | list[str]
    override_type: OverrideType
    override: Any
