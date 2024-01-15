[![Status Checks](https://github.com/skymantle-tech/skymantle-mock-data-forge/actions/workflows/status_checks.yml/badge.svg?branch=main)](https://github.com/skymantle-tech/skymantle-mock-data-forge/actions/workflows/status_checks.yml)

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

- `load_data` - will load data across all destinations or the destination of the provided forge ID
- `get_data` - will return data across all destinations or the data for the provided forge ID
- `add_key` - when new data is created through tests you can provide it's key so that it's included in the `cleanup_data` call
- `cleanup_data` - will remove data across all destinations or the destination of the provided forge ID

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

- Override specific data values at run time. Useful when config files are stored in static json files.

```python
from datetime import UTC, datetime
from skymantle_mock_data_forge.forge_factory import ForgeFactory
from skymantle_mock_data_forge.models import OverideType

config = [
    {
        "forge_id": "some_config_id",
        "dynamodb": {
            "table": {"name": "some_table"},
            "primary_key_names": ["PK"],
            "items": [{"PK": "some_key_1", "Description": "Some description 1", "CreateDate": ""}],
        },
    }
]

overrides = [
    {
        "key_paths": "CreateDate",
        "override_type": OverideType.REPLACE_VALUE,
        "override": datetime.now(UTC).isoformat(),
    }
]

factory = ForgeFactory(config, overrides=overrides)
factory.load_data("some_config_id")

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
                "key": "some_key_3", 
                "data": {"base64": "SGVsbG8gV29ybGQh"}
            },
            {
                "key": "some_key_4", 
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

## Overrides


In some cases it's easier to store config files in json for sharing. When coming from static sources, overrides allow data to be changed at runtime. this can be used for setting values like the AWS account id for the current context or the current date. The following type of modifications can be used:

- Replace Value
    - Will replace the value with a new one
    - For example if create date is current "" it can be replaced with "2023-01-01"
- Format Value
    - Will used pythons `str.format(*args)`
    - The original value must be a string, the replacement is index based.
    - For example if ddescription is "{} Assemble{}" it back be formated to "Avengers Assemble!"
- Call Function
    - will call a custom function when processing each item.
    - The signature of the funct is func(key: str, value: any, context: dict) -> any:
        - key - The current key (ie: CreateDate)
        - value - The current value for the given key
        - conext - The current item being built
        - return - the new value.

In the case of nested dictionaries, key paths are supported which are "." seperated, key paths will also traverse sub lists. Current it's not possible to specify an index, all items in the list will be updated. 

If the same overide is needed for multiple keys then a list of key paths can be used. Currently overrides only work with json structured data. 

The default behaviour for overrides is to ignore key path errors, however to alter this behaviour by setting the `DATA_FORGE_SUPPRESS_KEY_PATH_ERRORS` environment variable. Supported values are `0`, `false`, `no` and `off`.

### Example

```python
# Current config stored in full or in part in json files

[
    {
        "forge_id": "some_config_id",
        "dynamodb": {
            "table": {"name": "some_table"},
            "primary_key_names": ["pk"],
            "items": [
                {
                    "pk": "", 
                    "description": "Executed on {} Environment.",
                    "audit": { "create_date": "", "last_update_date": "" },
                    "items": [{"id":""},{"id":""}]
                },
                {
                    "pk": "", 
                    "description": "Executed on {} Environment.",
                    "audit": { "create_date": "", "last_update_date": "" },
                    "items": [{"id":""},{"id":""}]
                }
            ],
        },
    }
]

# Overrides

def generate_id(key: str, value: any, context: dict) -> any:
    return str(uuid.uuid4())

current_date = datetime.now(UTC).isoformat()
environment = os.environ.get("ENVIRONMENT")

overrides = [
    {
        "key_paths": [
            "pk",
            "items.id",
        ],
        "override_type": OverideType.CALL_FUNCTION,
        "override": generate_id,
    },
    {
        "key_paths": [
            "audit.create_date",
            "audit.last_update_date",
        ],
        "override_type": OverideType.REPLACE_VALUE,
        "override": current_date,
    },
    {
        "key_paths": "description",
        "override_type": OverideType.FORMAT_VALUE,
        "override": [environment],
    }
]

# The resulting data 

{
    "pk": "11184314-b3fd-4a2d-bf79-bb50eabc9985", 
    "description": "Executed on Test Environment.",
    "audit": { "create_date": "2024-01-06T22:59:00.469843+00:00", "last_update_date": "2024-01-06T22:59:00.469843+00:00" },
    "items": [
        {"id":"e61e4001-ac84-43fb-8ba4-0f2ca5972c83"},
        {"id":"9ea2d4ff-9a01-4ea6-95ea-4f6f01e797ca"}
    ]
},
{
    "pk": "91aa7686-6dbd-47a1-a779-891436fdfac0", 
    "description": "Executed on Test Environment.",
    "audit": { "create_date": "2024-01-06T22:59:00.469843+00:00", "last_update_date": "2024-01-06T22:59:00.469843+00:00" },
    "items": [
        {"id":"45aef30f-a6da-448b-bbac-2530f5aad558"},
        {"id":"65722f85-f799-4a85-9415-088bbcd55d8c"}
    ]
},
}

```

By default, the same list of overrides is distributed to all destinations, if an override needs to vary by destination a forge Id can be provided.

```python

overrides = [
    { # Will go to all destinations
        "key_paths": "data.text",
        "override_type": OverideType.REPLACE_VALUE,
        "override": "Some Other Data",
    },
    { # Will go to some_config_1
        "forge_id": "some_config_1",
        "key_paths": "PK",
        "override_type": OverideType.REPLACE_VALUE,
        "override": "some_other_key_1",
    },
    { # Will go to some_config_2
        "forge_id": "some_config_2",
        "key_paths": "PK",
        "override_type": OverideType.REPLACE_VALUE,
        "override": "some_other_key_2",
    }
]

```