import json
import os

import boto3
import pytest
from moto import mock_cloudformation, mock_s3, mock_ssm
from pytest_mock import MockerFixture

from skymantle_mock_data_forge.s3_forge import S3Forge


@pytest.fixture(autouse=True)
def environment(mocker: MockerFixture):
    return mocker.patch.dict(
        os.environ,
        {"AWS_DEFAULT_REGION": "us-east-1", "BOTO_BUDDY_DISABLE_CACHE": "true"},
    )


@mock_s3
@mock_ssm
def test_load_data_by_ssm():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    ssm_client = boto3.client("ssm")
    ssm_client.put_parameter(Name="some_ssm_key", Type="String", Value="some_bucket")

    s3_config = {
        "bucket": {"ssm": "some_ssm_key"},
        "s3_object": [{"key": "some_key", "data": {"text": "Some Data"}}],
    }

    manager = S3Forge("some-config", s3_config)
    manager.load_data()

    response = s3_client.get_object(Bucket="some_bucket", Key="some_key")
    assert response["Body"].read() == b"Some Data"


@mock_cloudformation
@mock_s3
def test_load_data_by_cfn():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    cfn_template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "sample template",
        "Resources": {},
        "Outputs": {"bucket_name": {"Value": "some_bucket"}},
    }

    cfn_client = boto3.client("cloudformation")
    cfn_client.create_stack(StackName="some_stack", TemplateBody=json.dumps(cfn_template))

    s3_config = {
        "bucket": {"stack": {"name": "some_stack", "output": "bucket_name"}},
        "s3_object": [{"key": "some_key", "data": {"text": "Some Data"}}],
    }

    manager = S3Forge("some-config", s3_config)
    manager.load_data()

    response = s3_client.get_object(Bucket="some_bucket", Key="some_key")
    assert response["Body"].read() == b"Some Data"


@mock_cloudformation
@mock_s3
def test_load_data_by_cfn_invalid_output():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    cfn_template = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "sample template",
        "Resources": {},
        "Outputs": {"wrong_bucket_name": {"Value": "some_bucket"}},
    }

    cfn_client = boto3.client("cloudformation")
    cfn_client.create_stack(StackName="some_stack", TemplateBody=json.dumps(cfn_template))

    s3_config = {
        "bucket": {"stack": {"name": "some_stack", "output": "bucket_name"}},
        "s3_object": [{"key": "some_key", "data": {"text": "Some Data"}}],
    }

    with pytest.raises(Exception) as e:
        S3Forge("some-config", s3_config)

    assert str(e.value) == "Unable to find a bucket_name for stack: some_stack and output: bucket_name"


@mock_s3
def test_load_text_and_cleanup_data():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_object": [{"key": "some_key", "data": {"text": "Some Data"}}],
    }

    manager = S3Forge("some-config", s3_config)
    manager.load_data()

    response = s3_client.get_object(Bucket="some_bucket", Key="some_key")
    assert response["Body"].read() == b"Some Data"

    manager.cleanup_data()

    with pytest.raises(Exception) as e:
        s3_client.get_object(Bucket="some_bucket", Key="some_key")

    assert "An error occurred (NoSuchKey) when calling the GetObject operation" in str(e.value)


@mock_s3
def test_load_json_and_cleanup_data():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_object": [{"key": "some_key", "data": {"json": {"some_key": "some_value"}}}],
    }

    manager = S3Forge("some-config", s3_config)
    manager.load_data()

    response = s3_client.get_object(Bucket="some_bucket", Key="some_key")
    assert response["Body"].read() == b'{"some_key": "some_value"}'

    manager.cleanup_data()

    with pytest.raises(Exception) as e:
        s3_client.get_object(Bucket="some_bucket", Key="some_key")

    assert "An error occurred (NoSuchKey) when calling the GetObject operation" in str(e.value)


@mock_s3
def test_load_base64_and_cleanup_data():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_object": [{"key": "some_key", "data": {"base64": "SGVsbG8gV29ybGQh"}}],
    }

    manager = S3Forge("some-config", s3_config)
    manager.load_data()

    response = s3_client.get_object(Bucket="some_bucket", Key="some_key")
    assert response["Body"].read() == b"Hello World!"

    manager.cleanup_data()

    with pytest.raises(Exception) as e:
        s3_client.get_object(Bucket="some_bucket", Key="some_key")

    assert "An error occurred (NoSuchKey) when calling the GetObject operation" in str(e.value)


@mock_s3
def test_load_csv_and_cleanup_data():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_object": [
            {
                "key": "some_key",
                "data": {
                    "csv": [
                        ["a", "b"],
                        ["c", "d"],
                        ["e", "f"],
                        [1, 2],
                    ]
                },
            }
        ],
    }

    manager = S3Forge("some-config", s3_config)
    manager.load_data()

    response = s3_client.get_object(Bucket="some_bucket", Key="some_key")
    assert response["Body"].read() == b"a,b\r\nc,d\r\ne,f\r\n1,2\r\n"

    manager.cleanup_data()

    with pytest.raises(Exception) as e:
        s3_client.get_object(Bucket="some_bucket", Key="some_key")

    assert "An error occurred (NoSuchKey) when calling the GetObject operation" in str(e.value)


@mock_s3
def test_load_data_invalid_type():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_object": [{"key": "some_key", "data": {"invalid": ""}}],
    }

    manager = S3Forge("some-config", s3_config)

    with pytest.raises(Exception) as e:
        manager.load_data()

    assert "Can only have one of the following per s3 config:" in str(e.value)


@mock_s3
def test_load_data_to_many_types():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_object": [
            {
                "key": "some_key",
                "data": {
                    "text": "Some Data",
                    "json": {"some_key": "some_value"},
                },
            }
        ],
    }

    manager = S3Forge("some-config", s3_config)

    with pytest.raises(Exception) as e:
        manager.load_data()

    assert "Can only have one of the following per s3 config:" in str(e.value)


@mock_s3
def test_get_data():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_object": [{"key": "some_key", "data": {"text": "Some Data"}}],
    }

    manager = S3Forge("some-config", s3_config)
    data = manager.get_data()

    assert data == [{"key": "some_key", "data": {"text": "Some Data"}}]


@mock_s3
def test_add_key_and_cleanup_data():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_object": [],
    }

    manager = S3Forge("some-config", s3_config)

    s3_client.put_object(Bucket="some_bucket", Key="some_key", Body=b"File Data")

    manager.add_key("some_key")
    manager.cleanup_data()

    with pytest.raises(Exception) as e:
        s3_client.get_object(Bucket="some_bucket", Key="some_key")

    assert "An error occurred (NoSuchKey) when calling the GetObject operation" in str(e.value)