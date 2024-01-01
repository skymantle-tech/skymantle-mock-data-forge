import json
import os

import boto3
import pytest
from moto import mock_cloudformation, mock_dynamodb, mock_ssm
from pytest_mock import MockerFixture

from skymantle_mock_data_forge.dynamodb_forge import DynamoDbForge


@pytest.fixture(autouse=True)
def environment(mocker: MockerFixture):
    return mocker.patch.dict(
        os.environ,
        {"AWS_DEFAULT_REGION": "ca-central-1"},
    )


@mock_ssm
@mock_dynamodb
def test_load_data_by_ssm():
    dynamodb_client = boto3.client("dynamodb", region_name="ca-central-1")

    dynamodb_client.create_table(
        BillingMode="PAY_PER_REQUEST",
        TableName="some_table",
        AttributeDefinitions=[{"AttributeName": "PK", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}],
    )

    ssm_client = boto3.client("ssm")
    ssm_client.put_parameter(Name="some_ssm_key", Type="String", Value="some_table")

    data_loader_config = {
        "table": {"ssm": "some_ssm_key"},
        "primary_key_names": ["PK"],
        "items": [{"PK": "some_key_1", "Description": "Some description 1"}],
    }

    manager = DynamoDbForge("some-config", data_loader_config)
    manager.load_data()

    response = dynamodb_client.get_item(TableName="some_table", Key={"PK": {"S": "some_key_1"}})
    assert response["Item"] == {"PK": {"S": "some_key_1"}, "Description": {"S": "Some description 1"}}


@mock_cloudformation
@mock_dynamodb
def test_load_data_by_cfn():
    dynamodb_client = boto3.client("dynamodb", region_name="ca-central-1")

    dynamodb_client.create_table(
        BillingMode="PAY_PER_REQUEST",
        TableName="some_table",
        AttributeDefinitions=[{"AttributeName": "PK", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}],
    )

    cfn_template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "sample template",
        "Resources": {},
        "Outputs": {"db_name": {"Value": "some_table"}},
    }

    cfn_client = boto3.client("cloudformation", region_name="ca-central-1")
    cfn_client.create_stack(StackName="some_stack", TemplateBody=json.dumps(cfn_template))

    data_loader_config = {
        "table": {"stack": {"name": "some_stack", "output": "db_name"}},
        "primary_key_names": ["PK"],
        "items": [{"PK": "some_key_1", "Description": "Some description 1"}],
    }

    manager = DynamoDbForge("some-config", data_loader_config)
    manager.load_data()

    response = dynamodb_client.get_item(TableName="some_table", Key={"PK": {"S": "some_key_1"}})
    assert response["Item"] == {"PK": {"S": "some_key_1"}, "Description": {"S": "Some description 1"}}


@mock_cloudformation
@mock_dynamodb
def test_load_data_by_cfn_invalid_output():
    dynamodb_client = boto3.client("dynamodb", region_name="ca-central-1")

    dynamodb_client.create_table(
        BillingMode="PAY_PER_REQUEST",
        TableName="some_table",
        AttributeDefinitions=[{"AttributeName": "PK", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}],
    )

    cfn_template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "sample template",
        "Resources": {},
        "Outputs": {"wrong_db_name": {"Value": "some_table"}},
    }

    cfn_client = boto3.client("cloudformation", region_name="ca-central-1")
    cfn_client.create_stack(StackName="some_stack", TemplateBody=json.dumps(cfn_template))

    data_loader_config = {
        "table": {"stack": {"name": "some_stack", "output": "db_name"}},
        "primary_key_names": ["PK"],
        "items": [{"PK": "some_key_1", "Description": "Some description 1"}],
    }

    with pytest.raises(Exception) as e:
        DynamoDbForge("some-config", data_loader_config)

    assert str(e.value) == "Unable to find a dynamodb_table for stack: some_stack and output: db_name"


@mock_dynamodb
def test_load_and_cleanup_data():
    dynamodb_client = boto3.client("dynamodb", region_name="ca-central-1")

    dynamodb_client.create_table(
        BillingMode="PAY_PER_REQUEST",
        TableName="some_table",
        AttributeDefinitions=[{"AttributeName": "PK", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}],
    )

    data_loader_config = {
        "table": {"name": "some_table"},
        "primary_key_names": ["PK"],
        "items": [{"PK": "some_key_1", "Description": "Some description 1"}],
    }

    manager = DynamoDbForge("some-config", data_loader_config)
    manager.load_data()

    response = dynamodb_client.get_item(TableName="some_table", Key={"PK": {"S": "some_key_1"}})
    assert response["Item"] == {"PK": {"S": "some_key_1"}, "Description": {"S": "Some description 1"}}

    manager.cleanup_data()

    response = dynamodb_client.get_item(TableName="some_table", Key={"PK": {"S": "some_key_1"}})
    assert response.get("Item") is None


@mock_dynamodb
def test_get_data():
    dynamodb_client = boto3.client("dynamodb", region_name="ca-central-1")

    dynamodb_client.create_table(
        BillingMode="PAY_PER_REQUEST",
        TableName="some_table",
        AttributeDefinitions=[{"AttributeName": "PK", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}],
    )

    data_loader_config = {
        "table": {"name": "some_table"},
        "primary_key_names": ["PK"],
        "items": [{"PK": "some_key_1", "Description": "Some description 1"}],
    }

    manager = DynamoDbForge("some-config", data_loader_config)
    data = manager.get_data()

    assert data == [{"PK": "some_key_1", "Description": "Some description 1"}]


@mock_dynamodb
def test_add_key_and_cleanup_data():
    dynamodb_client = boto3.client("dynamodb", region_name="ca-central-1")

    dynamodb_client.create_table(
        BillingMode="PAY_PER_REQUEST",
        TableName="some_table",
        AttributeDefinitions=[{"AttributeName": "PK", "AttributeType": "S"}],
        KeySchema=[{"AttributeName": "PK", "KeyType": "HASH"}],
    )

    data_loader_config = {
        "table": {"name": "some_table"},
        "primary_key_names": ["PK"],
        "items": [],
    }

    manager = DynamoDbForge("some-config", data_loader_config)

    response = dynamodb_client.put_item(
        TableName="some_table", Item={"PK": {"S": "some_key_1"}, "Description": {"S": "Some description 1"}}
    )

    manager.add_key({"PK": "some_key_1"})
    manager.cleanup_data()

    response = dynamodb_client.get_item(TableName="some_table", Key={"PK": {"S": "some_key_1"}})
    assert response.get("Item") is None
