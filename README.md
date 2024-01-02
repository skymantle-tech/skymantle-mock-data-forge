# Skymantle Mock Data Forge

A package for managing test data on aws resources, through configuration, when running integration and end-to-end tests in the cloud. Currently the package supports managing data on DynamoDb and S3.

The following project commands are supported:
- `make setup` - Installs all dependencies ands creates virtual environment
- `make unitTests` - runs unit tests
- `make lintAndAnalysis` - Runs [ruff](https://github.com/astral-sh/ruff), [bandit](https://github.com/PyCQA/bandit) and [black](https://github.com/psf/black)
- `make build` - Creates distribution

## Installation

Currently the package isn't on pypi, however the GitHub repo can be referenced directly in a requirements file.  For example:
- `skymantle_mock_data_forge @ git+https://github.com/skymantle-tech/skymantle-mock-data-forge@main`

## Usage

Use the forge factory to manage data to multiple destinations (any combination of DynamoDB tables and S3 buckets). An id is used to specify each unique destination. The forge factor provides the following functions:

- `load_data` - for the given forge ID load data in to the appropriate destination
- `get_data` - for the given forge ID returns the data collection from the configuration
- `add_key` - when new data is created through tests you can provide their key so that it's included in the cleanup is called
- `cleanup_data` - for the given forge ID remove test data from the appropriate destination

### Examples

- manage data in DynamoDB, assumes `AWS_PROFILE` environment variable is set

```python
from skymantle_mock_data_forge.forge_factory import ForgeFactory

config = [
    {
        "forge_id": "some_config_id",
        "dynamodb": {
            "table": {"name": "some_table"},
            "primary_key_names": ["PK"],
            "items": [{"PK": "some_key_1", "Description": "Some description 1"}],
        },
    }
]

factory = ForgeFactory(config)
factory.load_data("some_config_id")

# perform tests

factory.add_key("some_config_id", {"PK": "some_key_2"})
factory.cleanup_data("some_config_id")
```

- Managing multiple destinations

```python
from skymantle_mock_data_forge.forge_factory import ForgeFactory

config = [
    {
        "forge_id": "some_config_id_1",
        "dynamodb": {
            "table": {"name": "some_table"},
            "primary_key_names": ["PK"],
            "items": [{"PK": "some_key_1", "Description": "Some description 1"}],
        },
    },
    {
        "forge_id": "some_config_id_2",
        "s3": {
            "bucket": {"name": "some_bucket"},
            "s3_objects": [{"key": "some_key", "data": {"base64": "SGVsbG8gV29ybGQh"}}],
        },
    }
]

factory = ForgeFactory(config)
factory.load_data("some_config_id_1")
factory.load_data("some_config_id_2")

# ...
```

- provide forge factory with an AWS session

```python
from boto3 import Session
# ...

session = Session(profile_name="developer")
factory = ForgeFactory(config, session)

# ...
```

## Configuration

The forge factory takes a list of configuration, each item in the lists must represent a single destination, either DynamoDB or S3.

For the DynamoDb configuration, the table name can be specific or  proviced through an SSM parameter or the output of a CloutFormation stack

- By table name

```json
{
    "forge_id": "some_config_id_1",
    "dynamodb": {
        "table": {"name": "some_table"},
        "primary_key_names": ["PK"],
        "items": [{"PK": "some_key_1", "Description": "Some description 1"}]
    }
}
```

- By SSM paramter

```json
{
    "forge_id": "some_config_id_1",
    "dynamodb": {
        "table": {"ssm": "ssm_parameter_key"},
        "primary_key_names": ["PK"],
        "items": [{"PK": "some_key_1", "Description": "Some description 1"}]
    }
}
```

- By CloudFormation stack output

```json
{
    "forge_id": "some_config_id_1",
    "dynamodb": {
        "table": {
            "stack": {
                "name": "cfn_stack_name",
                "output": "table_output_name"
            }
        },
        "primary_key_names": ["PK"],
        "items": [{"PK": "some_key_1", "Description": "Some description 1"}]
    }
}
```


For the S3 configuration, the bucket name can be specific or  provided through an SSM parameter or the output of a CloudFormation stack (similar to DynamoDB). 

The following object data is supported:
- text
- json
- base64
- csv

```json
{
    "forge_id": "some_config_id_1",
    "s3": {
        "bucket": {"name": "some_bucket"},
        "s3_objects": [
            {
                "key": "some_key_1", 
                "data": {"text": "Some Data"}
            },
            {
                "key": "some_key_2", 
                "data": {"json": {"some_key": "some_value"}}
            },
            {
                "key": "some_key_2", 
                "data": {"base64": "SGVsbG8gV29ybGQh"}
            },
            {
                "key": "some_key_2", 
                "data": {
                    "csv": [
                        ["a", "b"],
                        ["c", "d"],
                        ["e", "f"],
                        [1, 2],
                    ]
                }
            }
        ]
    }
}
```