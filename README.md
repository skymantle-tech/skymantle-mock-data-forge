[![Status Checks](https://github.com/skymantle-tech/skymantle-mock-data-forge/actions/workflows/status_checks.yml/badge.svg?branch=main)](https://github.com/skymantle-tech/skymantle-mock-data-forge/actions/workflows/status_checks.yml)

# Skymantle Mock Data Forge

A package for managing test data on aws resources through configuration, when running integration and end-to-end tests in the cloud. Currently the package supports managing data on DynamoDb and S3.

## Installation
To install use:

```
pip3 install skymantle_mock_data_forge
```

## Usage

Use the forge factory to manage data to multiple destinations (any combination of DynamoDB tables and S3 buckets). An id is used to specify each unique destination. The forge factor provides the following functions:

- `load_data` - will load data across all destinations or the destination of the provided forge ID
- `get_data` - will return data across all destinations or the data for the provided forge ID, will only return data created by the forge
- `get_data_first_item` - will return first item of data across all destinations or the data for the provided forge ID, will only return data created by the forge
- `add_key` - when new data is created through tests you can provide it's key so that it's included in the `cleanup_data` call
- `cleanup_data` - will remove data across all destinations or the destination of the provided forge ID

### Examples

- manage data in DynamoDB, assumes aws credentials environment variable are set, such as `AWS_PROFILE`

```python
from skymantle_mock_data_forge.forge_factory import ForgeFactory

config = [
    {
        "forge_id": "some_config_id",
        "dynamodb": {
            "table": {"name": "some_table"},
            "primary_key_names": ["PK"],
            "items": [{"data": {"PK": "some_key_1", "Description": "Some description 1"}}],
        },
    }
]

factory = ForgeFactory(config)
factory.load_data()

# perform tests

factory.add_key("some_config_id", {"PK": "some_key_2"})
factory.cleanup_data()
```

-  Load config from a json file

```python
from skymantle_mock_data_forge.forge_factory import ForgeFactory

factory = ForgeFactory("path/to/file.json")
factory.load_data()

# perform tests

factory.add_key("some_config_id", {"PK": "some_key_2"})
factory.cleanup_data()
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
            "items": [{"data": {"PK": "some_key_1", "Description": "Some description 1"}}],
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

# To load a single destination
factory.load_data("some_config_id_2")

# To load all destinations
factory.load_data()

# ...
```

- Provide forge factory with an AWS session

```python
from boto3 import Session
# ...

session = Session(profile_name="developer")
factory = ForgeFactory(config, session)

# ...
```

- Use queries to get specific data for use in tests by querying custom tags.

```python
from datetime import UTC, datetime
from skymantle_mock_data_forge.forge_factory import ForgeFactory

config = [
    {
        "forge_id": "some_config_id",
        "dynamodb": {
            "table": {"name": "some_table"},
            "primary_key_names": ["PK"],
            "items": [
                {
                    "tags": {
                        "tests": [
                            "test_get_items", 
                            "test_get_item", 
                            "test_update_item",
                        ],
                    },
                    "data": {"PK": "some_key_1", "Description": "Some description 1"},
                },
                {
                    "tags": {"tests": "test_item_delete"},
                    "data": {"PK": "some_key_2", "Description": "Some description 2"},
                },
            ],
        },
    }
]

factory = ForgeFactory(config, overrides=overrides)
factory.load_data()

#...
# Unit test for deleting an item

data = factory.get_data(query={"StringEquals": {"tests": "test_item_delete"}})
pK_to_delete = data[0]["data"]["PK]

#...
```

- Override specific values at run time. Useful when config files are stored in static json files or handling dates

```python
from datetime import UTC, datetime
from skymantle_mock_data_forge.forge_factory import ForgeFactory
from skymantle_mock_data_forge.models import OverrideType

config = [
    {
        "forge_id": "some_config_id",
        "dynamodb": {
            "table": {"name": "some_table"},
            "primary_key_names": ["PK"],
            "items": [{"data": {"PK": "some_key_1", "Description": "Some description 1", "CreateDate": ""}}],
        },
    }
]

overrides = [
    {
        "key_paths": "CreateDate",
        "override_type": OverrideType.REPLACE_VALUE,
        "override": datetime.now(UTC).isoformat(),
    }
]

factory = ForgeFactory(config, overrides=overrides)
factory.load_data("some_config_id")

# ...
```


## Configuration

The forge factory takes a list of configuration, each item in the lists must represent a single destination, either DynamoDB or S3.

For the DynamoDb configuration, the table name can be specific or  provided through an SSM parameter or the output of a CloudFormation stack

- By table name

```json
{
    "forge_id": "some_config_id_1",
    "dynamodb": {
        "table": {"name": "some_table"},
        "primary_key_names": ["PK"],
        "items": [{"data": {"PK": "some_key_1", "Description": "Some description 1"}}],
    }
}
```

- By SSM parameter

```json
{
    "forge_id": "some_config_id_1",
    "dynamodb": {
        "table": {"ssm": "ssm_parameter_key"},
        "primary_key_names": ["PK"],
        "items": [{"data": {"PK": "some_key_1", "Description": "Some description 1"}}],
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
        "items": [{"data": {"PK": "some_key_1", "Description": "Some description 1"}}],
    }
}
```


For the S3 configuration, the bucket name can be specific or  provided through an SSM parameter or the output of a CloudFormation stack (similar to DynamoDB). 

The following object data is supported:
- text
- json
- base64
- csv
- file

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
            },
            {
                "key": "some_key_5", 
                "data": {"file": "path/to/file"}
            },
        ]
    }
}
```

## Querying Data For Testing

Custom tags can be added to data that is managed by the forges, this will make it possible to categorize and group data for use during tests. Tags are completely optional, but required for querying.

- DynamoDB tag example
```json
[
    {
        "tags": {
            "tests": ["test_get_item", "test_update_item"]
        },
        "data": {"PK": "some_key_1", "Description": "Some description 1"},
    },
    {
        "tags": {"tests": "test_item_delete"},
        "data": {"PK": "some_key_2", "Description": "Some description 2"},
    },
]
```

- S3 tag example
```json
[
    {
        "key": "some_key_1",
        "tags": {"type": "text", "tests": ["test_1", "test_2"], "segment": "reporting"},
        "data": {"text": "Some Data"},
    },
    {
        "key": "some_key_2",
        "tags": {"type": "json", "tests": "test_3"},
        "data": {"json": {"key": "value"}},
    }
]
```

A query is made up of an operator and 1 or more condition key/value pairs. Supported operators are:

 - StringEquals - the value for the tag must match exactly to one of the items in the specified tag
 - StringLike - the value must be contained in on of the items in the specified tag

 It's also possible to use both operators in the query. When dealing with multiple conditions and/or operators, queries are limited to logical `AND` queries.

 ### Examples

For the data provided
 ``` json
[
    {
        "tags": {
            "record_type": "person",
            "tests": [
                "test_get_items", 
                "test_get_item", 
                "test_update_item"
            ]
        },
        "data": {"PK": "some_key_1", "Description": "Some description 1"}
    },
    {
        "tags": {
            "record_type": "building",
            "tests": [
                "test_get_items", 
                "test_get_item", 
                "test_update_item"
            ]
        },
        "data": {"PK": "some_key_2", "Description": "Some description 2"}
    },
    {
        "tags": {
            "record_type": "building",
            "tests": "item_delete"
        },
        "data": {"PK": "some_key_2", "Description": "Some description 2"}
    }
]
```

- `{"StringLike": {"tests": "get"}}` will return

```json
[
    {
        "tags": {
            "record_type": "person",
            "tests": [
                "test_get_items", 
                "test_get_item", 
                "test_update_item"
            ]
        },
        "data": {"PK": "some_key_1", "Description": "Some description 1"}
    },
    {
        "tags": {
            "record_type": "building",
            "tests": [
                "test_get_items", 
                "test_get_item", 
                "test_update_item"
            ]
        },
        "data": {"PK": "some_key_2", "Description": "Some description 2"}
    }
]
```

- `{"StringEquals": {"tests": "test_get_item", "record_type": "building"}}` will return

```json
[
    {
        "tags": {
            "record_type": "building",
            "tests": [
                "test_get_items", 
                "test_get_item", 
                "test_update_item"
            ]
        },
        "data": {"PK": "some_key_2", "Description": "Some description 2"}
    }
]
```

- `{"StringEquals": {"record_type": "building"}, "StringLike": {"tests": "test"}}` will return

```json
[
    {
        "tags": {
            "record_type": "building",
            "tests": [
                "test_get_items", 
                "test_get_item", 
                "test_update_item"
            ]
        },
        "data": {"PK": "some_key_2", "Description": "Some description 2"}
    }
]
```

## Overrides


In some cases it's easier to store config files in json for sharing. When coming from static sources, overrides allow data to be changed at runtime. this can be used for setting values like the AWS account id for the current context or the current date. The following type of modifications can be used:

- Replace Value
    - Will replace the value with a new one
    - For example if create date is current "" it can be replaced with "2023-01-01"
- Format Value
    - Will used pythons `str.format(*args)`
    - The original value must be a string, the replacement is index based.
    - For example if description is "{} Assemble{}" it back be formatted to "Avengers Assemble!"
- Call Function
    - will call a custom function when processing each item.
    - The signature of the function is func(key: str, value: any, context: dict) -> any:
        - key - The current key (ie: CreateDate)
        - value - The current value for the given key
        - context - The current item being built
        - return - the new value.

In the case of nested dictionaries, key paths are supported which are "." separated, key paths will also traverse sub lists. Currently it's not possible to specify an index, all items in the list will be updated. 

If the same override is needed for multiple keys then a list of key paths can be used. Currently overrides only work with json structured data. 

The default behaviour for overrides is to ignore key path errors, however this behaviour can be altered by setting the `DATA_FORGE_SUPPRESS_KEY_PATH_ERRORS` environment variable. Supported values are `0`, `false`, `no` and `off`.

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
                    "data": {
                        "pk": "", 
                        "description": "Executed on {0} Environment.",
                        "audit": { "create_date": "", "last_update_date": "" },
                        "items": [{"id":""}, {"id":""}]
                    }
                },
                {
                    "data": {
                        "pk": "", 
                        "description": "Executed on {0} Environment.",
                        "audit": { "create_date": "", "last_update_date": "" },
                        "items": [{"id":""}, {"id":""}]
                    }
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
            "data.pk",
            "data.items.id",
        ],
        "override_type": OverrideType.CALL_FUNCTION,
        "override": generate_id,
    },
    {
        "key_paths": [
            "data.audit.create_date",
            "data.audit.last_update_date",
        ],
        "override_type": OverrideType.REPLACE_VALUE,
        "override": current_date,
    },
    {
        "key_paths": "data.description",
        "override_type": OverrideType.FORMAT_VALUE,
        "override": [environment],
    }
]

# The resulting data 

{
    "data": {
        "pk": "11184314-b3fd-4a2d-bf79-bb50eabc9985", 
        "description": "Executed on Test Environment.",
        "audit": { "create_date": "2024-01-06T22:59:00.469843+00:00", "last_update_date": "2024-01-06T22:59:00.469843+00:00" },
        "items": [
            {"id":"e61e4001-ac84-43fb-8ba4-0f2ca5972c83"},
            {"id":"9ea2d4ff-9a01-4ea6-95ea-4f6f01e797ca"}
        ]
    }
},
{
    "data": {
        "pk": "91aa7686-6dbd-47a1-a779-891436fdfac0", 
        "description": "Executed on Test Environment.",
        "audit": { "create_date": "2024-01-06T22:59:00.469843+00:00", "last_update_date": "2024-01-06T22:59:00.469843+00:00" },
        "items": [
            {"id":"45aef30f-a6da-448b-bbac-2530f5aad558"},
            {"id":"65722f85-f799-4a85-9415-088bbcd55d8c"}
        ]
    }
},


```

By default, the same list of overrides is distributed to all destinations, if an override needs to vary by destination a forge Id can be provided.

```python

overrides = [
    { # Will go to all destinations
        "key_paths": "data.text",
        "override_type": OverrideType.REPLACE_VALUE,
        "override": "Some Other Data",
    },
    { # Will go to some_config_1
        "forge_id": "some_config_1",
        "key_paths": "PK",
        "override_type": OverrideType.REPLACE_VALUE,
        "override": "some_other_key_1",
    },
    { # Will go to some_config_2
        "forge_id": "some_config_2",
        "key_paths": "PK",
        "override_type": OverrideType.REPLACE_VALUE,
        "override": "some_other_key_2",
    }
]

```

## Source Code Dev Notes

The following project commands are supported:
- `make` - provides command line help
- `make clean` - cleans out virtual env and distribution folder
- `make install` - Installs virtual env and required packages
- `make unit_tests` - runs unit tests
- `make lint_and_analysis` - Runs [ruff](https://github.com/astral-sh/ruff), [bandit](https://github.com/PyCQA/bandit) and [black](https://github.com/psf/black)
- `make build` - Creates distribution
