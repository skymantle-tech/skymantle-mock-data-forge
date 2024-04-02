import json
import os

import boto3
import pytest
from moto import mock_aws
from pytest_mock import MockerFixture

from skymantle_mock_data_forge.models import OverrideType
from skymantle_mock_data_forge.s3_forge import S3Forge


@pytest.fixture(autouse=True)
def environment(mocker: MockerFixture):
    return mocker.patch.dict(
        os.environ,
        {"AWS_DEFAULT_REGION": "us-east-1", "BOTO_BUDDY_DISABLE_CACHE": "true"},
    )


@mock_aws
def test_load_data_by_ssm():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    ssm_client = boto3.client("ssm")
    ssm_client.put_parameter(Name="some_ssm_key", Type="String", Value="some_bucket")

    s3_config = {
        "bucket": {"ssm": "some_ssm_key"},
        "s3_objects": [{"key": "some_key", "data": {"text": "Some Data"}}],
    }

    manager = S3Forge("some-config", s3_config)
    manager.load_data()

    response = s3_client.get_object(Bucket="some_bucket", Key="some_key")
    assert response["Body"].read() == b"Some Data"


@mock_aws
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
        "s3_objects": [{"key": "some_key", "data": {"text": "Some Data"}}],
    }

    manager = S3Forge("some-config", s3_config)
    manager.load_data()

    response = s3_client.get_object(Bucket="some_bucket", Key="some_key")
    assert response["Body"].read() == b"Some Data"


@mock_aws
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
        "s3_objects": [{"key": "some_key", "data": {"text": "Some Data"}}],
    }

    forge = S3Forge("some-config", s3_config)
    with pytest.raises(Exception) as e:
        forge.load_data()

    assert str(e.value) == "Unable to find a resource for stack: some_stack and output: bucket_name"


@mock_aws
def test_load_text_and_cleanup_data():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [{"key": "some_key", "data": {"text": "Some Data"}}],
    }

    manager = S3Forge("some-config", s3_config)
    manager.load_data()

    response = s3_client.get_object(Bucket="some_bucket", Key="some_key")
    assert response["Body"].read() == b"Some Data"

    manager.cleanup_data()

    with pytest.raises(Exception) as e:
        s3_client.get_object(Bucket="some_bucket", Key="some_key")

    assert "An error occurred (NoSuchKey) when calling the GetObject operation" in str(e.value)


@mock_aws
def test_load_json_and_cleanup_data():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [{"key": "some_key", "data": {"json": {"some_key": "some_value"}}}],
    }

    manager = S3Forge("some-config", s3_config)
    manager.load_data()

    response = s3_client.get_object(Bucket="some_bucket", Key="some_key")
    assert response["Body"].read() == b'{"some_key": "some_value"}'

    manager.cleanup_data()

    with pytest.raises(Exception) as e:
        s3_client.get_object(Bucket="some_bucket", Key="some_key")

    assert "An error occurred (NoSuchKey) when calling the GetObject operation" in str(e.value)


@mock_aws
def test_load_base64_and_cleanup_data():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [{"key": "some_key", "data": {"base64": "SGVsbG8gV29ybGQh"}}],
    }

    manager = S3Forge("some-config", s3_config)
    manager.load_data()

    response = s3_client.get_object(Bucket="some_bucket", Key="some_key")
    assert response["Body"].read() == b"Hello World!"

    manager.cleanup_data()

    with pytest.raises(Exception) as e:
        s3_client.get_object(Bucket="some_bucket", Key="some_key")

    assert "An error occurred (NoSuchKey) when calling the GetObject operation" in str(e.value)


@mock_aws
def test_load_csv_and_cleanup_data():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [
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


@mock_aws
def test_load_file_and_cleanup_data():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [
            {
                "key": "some_key",
                "data": {"file": "tests/data/amazon_web_services_logo.png"},
            }
        ],
    }

    manager = S3Forge("some-config", s3_config)
    manager.load_data()

    with open("tests/data/amazon_web_services_logo.png", "rb") as file:
        data = file.read()

    response = s3_client.get_object(Bucket="some_bucket", Key="some_key")
    assert response["Body"].read() == data

    manager.cleanup_data()

    with pytest.raises(Exception) as e:
        s3_client.get_object(Bucket="some_bucket", Key="some_key")

    assert "An error occurred (NoSuchKey) when calling the GetObject operation" in str(e.value)


@mock_aws
def test_load_data_invalid_type():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [{"key": "some_key", "data": {"invalid": ""}}],
    }

    manager = S3Forge("some-config", s3_config)

    with pytest.raises(Exception) as e:
        manager.load_data()

    assert "Can only have one of the following per s3 config:" in str(e.value)


@mock_aws
def test_load_data_to_many_types():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [
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


@mock_aws
def test_get_data():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [{"key": "some_key", "data": {"text": "Some Data"}}],
    }

    manager = S3Forge("some-config", s3_config)
    data = manager.get_data(query=None, return_source=True)

    assert data == [{"key": "some_key", "data": {"text": "Some Data"}}]


@mock_aws
def test_get_data_query_string_equals():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [
            {
                "key": "some_key_1",
                "tags": {"type": "text"},
                "data": {"text": "Some Data"},
            },
            {
                "key": "some_key_2",
                "tags": {"type": "json"},
                "data": {"json": {"some_key": "some_value"}},
            },
        ],
    }

    query = {"StringEquals": {"type": "text"}}

    manager = S3Forge("some-config", s3_config)
    data = manager.get_data(query=query, return_source=True)

    assert data == [{"key": "some_key_1", "tags": {"type": "text"}, "data": {"text": "Some Data"}}]


@mock_aws
def test_get_data_query_string_equals_list():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [
            {
                "key": "some_key_1",
                "tags": {"type": "text", "tests": ["test_1", "test_2"]},
                "data": {"text": "Some Data"},
            },
            {
                "key": "some_key_2",
                "tags": {"type": "json", "tests": "test_3"},
                "data": {"json": {"some_key": "some_value"}},
            },
        ],
    }
    query = {"StringEquals": {"tests": "test_1"}}

    manager = S3Forge("some-config", s3_config)
    data = manager.get_data(query=query, return_source=True)

    assert data == [
        {"key": "some_key_1", "tags": {"type": "text", "tests": ["test_1", "test_2"]}, "data": {"text": "Some Data"}},
    ]


@mock_aws
def test_get_data_query_string_like():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [
            {
                "key": "some_key_1",
                "tags": {"type": "text", "tests": ["test_1", "test_2"]},
                "data": {"text": "Some Data"},
            },
            {
                "key": "some_key_2",
                "tags": {"type": "json", "tests": "test_3"},
                "data": {"json": {"key": "value"}},
            },
            {
                "key": "some_key_3",
                "tags": {"type": "json"},
                "data": {"json": {"key": "value"}},
            },
        ],
    }
    query = {"StringLike": {"tests": "test"}}

    manager = S3Forge("some-config", s3_config)
    data = manager.get_data(query=query, return_source=True)

    assert data == [
        {"key": "some_key_1", "tags": {"type": "text", "tests": ["test_1", "test_2"]}, "data": {"text": "Some Data"}},
        {"key": "some_key_2", "tags": {"type": "json", "tests": "test_3"}, "data": {"json": {"key": "value"}}},
    ]


@mock_aws
def test_get_data_query_compound():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [
            {
                "key": "some_key_1",
                "tags": {"type": "text", "tests": ["test_1", "test_2"]},
                "data": {"text": "Some Data"},
            },
            {
                "key": "some_key_2",
                "tags": {"type": "json", "tests": "test_3"},
                "data": {"json": {"some_key": "some_value"}},
            },
            {
                "key": "some_key_3",
                "tags": {"type": "text"},
                "data": {"text": "Some Data"},
            },
        ],
    }
    query = {
        "StringLike": {"tests": "test"},
        "StringEquals": {"type": "text"},
    }

    manager = S3Forge("some-config", s3_config)
    data = manager.get_data(query=query, return_source=True)

    assert data == [
        {"key": "some_key_1", "tags": {"type": "text", "tests": ["test_1", "test_2"]}, "data": {"text": "Some Data"}}
    ]


@mock_aws
def test_get_data_query_no_matches():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [
            {"key": "some_key_1", "tags": {"type": "text"}, "data": {"text": "Some Data"}},
        ],
    }
    query = {
        "StringEquals": {"type": "json"},
    }

    manager = S3Forge("some-config", s3_config)
    data = manager.get_data(query=query, return_source=True)

    assert data == []


@mock_aws
def test_get_data_query_no_matches_list():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [
            {
                "key": "some_key_1",
                "tags": {"type": "text", "tests": ["test_1", "test_2"]},
                "data": {"text": "Some Data"},
            },
        ],
    }
    query = {
        "StringEquals": {"tests": "test_3"},
    }

    manager = S3Forge("some-config", s3_config)
    data = manager.get_data(query=query, return_source=True)

    assert data == []


@mock_aws
def test_get_data_query_invalid_operator():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [{"key": "some_key_1", "tags": {"type": "text"}, "data": {"text": "Some Data"}}],
    }

    query = {"StringNotEquals": {"type": "text"}}

    manager = S3Forge("some-config", s3_config)

    with pytest.raises(Exception) as e:
        manager.get_data(query=query, return_source=True)

    assert "Only the following query operators are supported:" in str(e.value)


@mock_aws
def test_get_data_empty_query():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [{"key": "some_key_1", "tags": {"type": "text"}, "data": {"text": "Some Data"}}],
    }

    query = {}

    manager = S3Forge("some-config", s3_config)

    with pytest.raises(Exception) as e:
        manager.get_data(query=query, return_source=True)

    assert str(e.value) == "Missing operator from query"


@mock_aws
def test_get_data_query_invalid_condition():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [{"key": "some_key_1", "tags": {"type": "text"}, "data": {"text": "Some Data"}}],
    }

    query = {"StringEquals": "condition"}

    manager = S3Forge("some-config", s3_config)

    with pytest.raises(Exception) as e:
        manager.get_data(query=query, return_source=True)

    assert str(e.value) == "The condition for an operator must be a dict."


@mock_aws
def test_get_data_query_multiple_condition():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [
            {
                "key": "some_key_1",
                "tags": {"type": "text", "tests": ["test_1", "test_2"]},
                "data": {"text": "Some Data"},
            },
            {
                "key": "some_key_2",
                "tags": {"type": "json", "tests": "test_3"},
                "data": {"json": {"key": "value"}},
            },
            {
                "key": "some_key_3",
                "tags": {"type": "text"},
                "data": {"text": "Some Data"},
            },
        ],
    }
    query = {"StringEquals": {"type": "text", "tests": "test_1"}}

    manager = S3Forge("some-config", s3_config)

    data = manager.get_data(query=query, return_source=True)

    assert data == [
        {"key": "some_key_1", "tags": {"type": "text", "tests": ["test_1", "test_2"]}, "data": {"text": "Some Data"}}
    ]


@mock_aws
def test_get_data_exclude_tags():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [
            {
                "key": "some_key_1",
                "tags": {"type": "text", "tests": ["test_1", "test_2"]},
                "data": {"text": "Some Data"},
            },
            {
                "key": "some_key_2",
                "tags": {"type": "json", "tests": "test_3"},
                "data": {"json": {"key": "value"}},
            },
            {
                "key": "some_key_3",
                "tags": {"type": "text"},
                "data": {"text": "Some Data"},
            },
        ],
    }
    query = {"StringEquals": {"type": "text", "tests": "test_1"}}

    manager = S3Forge("some-config", s3_config)

    data = manager.get_data(query=query, return_source=False)

    assert data == [{"key": "some_key_1", "data": {"text": "Some Data"}}]


@mock_aws
def test_get_data_query_invalid_tag_int():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [{"key": "some_key_1", "tags": {"type": 0}, "data": {"text": "Some Data"}}],
    }

    query = {"StringEquals": {"type": "text"}}

    manager = S3Forge("some-config", s3_config)

    with pytest.raises(Exception) as e:
        manager.get_data(query=query, return_source=True)

    assert str(e.value) == "Tag values can only be strings or list of strings."


@mock_aws
def test_get_data_query_invalid_tag_list():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [{"key": "some_key_1", "tags": {"type": [0]}, "data": {"text": "Some Data"}}],
    }

    query = {"StringEquals": {"type": "text"}}

    manager = S3Forge("some-config", s3_config)

    with pytest.raises(Exception) as e:
        manager.get_data(query=query, return_source=True)

    assert str(e.value) == "Tag values can only be strings or list of strings."


@mock_aws
def test_add_key_and_cleanup_data():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [],
    }

    manager = S3Forge("some-config", s3_config)

    s3_client.put_object(Bucket="some_bucket", Key="some_key", Body=b"File Data")

    manager.add_key("some_key")
    manager.cleanup_data()

    with pytest.raises(Exception) as e:
        s3_client.get_object(Bucket="some_bucket", Key="some_key")

    assert "An error occurred (NoSuchKey) when calling the GetObject operation" in str(e.value)


@mock_aws
def test_override():
    s3_client = boto3.client("s3")
    s3_client.create_bucket(Bucket="some_bucket")

    s3_config = {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [
            {
                "key": "some_key",
                "data": {"json": {"some_key": "some_value"}},
            }
        ],
    }

    overrides = [
        {
            "key_paths": "data.json.some_key",
            "override_type": OverrideType.REPLACE_VALUE,
            "override": "some_other_value",
        },
    ]

    manager = S3Forge("some-config", s3_config, overrides=overrides)
    manager.load_data()

    response = s3_client.get_object(Bucket="some_bucket", Key="some_key")
    assert response["Body"].read() == b'{"some_key": "some_other_value"}'

    data = manager.get_data(query=None, return_source=True)
    assert data == [{"key": "some_key", "data": {"json": {"some_key": "some_other_value"}}}]
