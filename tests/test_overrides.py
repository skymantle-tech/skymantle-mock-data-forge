import os
import uuid
from datetime import UTC, datetime

import pytest
from pytest_mock import MockerFixture

from skymantle_mock_data_forge.base_forge import BaseForge
from skymantle_mock_data_forge.models import OverrideType


@pytest.fixture(autouse=True)
def environment(mocker: MockerFixture):
    return mocker.patch.dict(
        os.environ,
        {"AWS_DEFAULT_REGION": "us-east-1", "BOTO_BUDDY_DISABLE_CACHE": "true"},
    )


def test_no_override():
    data = [{"id": "project_1"}, {"id": "project_2"}]

    forge = BaseForge("string")
    update_data = forge._override_data(data)

    assert update_data == data


def test_replace_value():
    data = [{"create_date": ""}, {"create_date": ""}]

    current_date = datetime.now(UTC).isoformat()
    overrides = [
        {
            "key_paths": "create_date",
            "override_type": OverrideType.REPLACE_VALUE,
            "override": current_date,
        }
    ]

    forge = BaseForge("string", overrides)
    update_data = forge._override_data(data)

    assert update_data == [{"create_date": current_date}, {"create_date": current_date}]


def test_format_value():
    data = [{"key_1": "{} Assemble!"}]

    overrides = [
        {
            "key_paths": "key_1",
            "override_type": OverrideType.FORMAT_VALUE,
            "override": ["Avengers"],
        }
    ]

    forge = BaseForge("string", overrides)
    update_data = forge._override_data(data)

    assert update_data == [{"key_1": "Avengers Assemble!"}]


def test_call_function():
    new_ids = []

    func_key = []
    func_value = []
    func_context = []

    def generate_id(key: str, value: any, context: dict) -> any:
        nonlocal new_ids
        nonlocal func_key
        nonlocal func_value
        nonlocal func_context

        func_key.append(key)
        func_value.append(value)
        func_context.append(context)

        new_id = str(uuid.uuid4())
        new_ids.append(new_id)

        return new_id

    data = [{"id": "old1"}, {"id": "old2"}]

    overrides = [
        {
            "key_paths": "id",
            "override_type": OverrideType.CALL_FUNCTION,
            "override": generate_id,
        }
    ]

    forge = BaseForge("string", overrides)
    update_data = forge._override_data(data)

    assert new_ids[0] != new_ids[1]
    assert update_data == [{"id": new_ids[0]}, {"id": new_ids[1]}]

    assert func_key == ["id", "id"]
    assert func_value == ["old1", "old2"]
    assert func_context == [{"id": "old1"}, {"id": "old2"}]


def test_key_path_list():
    data = [{"create_date": "", "update_date": ""}]

    current_date = datetime.now(UTC).isoformat()
    overrides = [
        {
            "key_paths": ["create_date", "update_date"],
            "override_type": OverrideType.REPLACE_VALUE,
            "override": current_date,
        }
    ]

    forge = BaseForge("string", overrides)
    update_data = forge._override_data(data)

    assert update_data == [{"create_date": current_date, "update_date": current_date}]


def test_multi_level_key_path():
    data = [{"key": "", "audit": {"create_date": ""}}]

    current_date = datetime.now(UTC).isoformat()
    key = str(uuid.uuid4())

    overrides = [
        {
            "key_paths": "key",
            "override_type": OverrideType.REPLACE_VALUE,
            "override": key,
        },
        {
            "key_paths": "audit.create_date",
            "override_type": OverrideType.REPLACE_VALUE,
            "override": current_date,
        },
    ]

    forge = BaseForge("string", overrides)
    update_data = forge._override_data(data)

    assert update_data == [{"key": key, "audit": {"create_date": current_date}}]


def test_nested_lists():
    data = [{"id": "", "items": [{"id": ""}, {"id": ""}, {"id": ""}]}]

    key = str(uuid.uuid4())

    overrides = [
        {
            "key_paths": ["id", "items.id"],
            "override_type": OverrideType.REPLACE_VALUE,
            "override": key,
        },
    ]

    forge = BaseForge("string", overrides)
    update_data = forge._override_data(data)

    assert update_data == [{"id": key, "items": [{"id": key}, {"id": key}, {"id": key}]}]


def test_nested_lists_empty():
    data = [{"id": "", "items": []}]

    key = str(uuid.uuid4())

    overrides = [
        {
            "key_paths": ["id", "items.id"],
            "override_type": OverrideType.REPLACE_VALUE,
            "override": key,
        },
    ]

    forge = BaseForge("string", overrides)
    update_data = forge._override_data(data)

    assert update_data == [{"id": key, "items": []}]


def test_nested_lists_invalid():
    os.environ["DATA_FORGE_SUPPRESS_KEY_PATH_ERRORS"] = "false"

    data = [{"id": "", "items": ["id", "id", "id"]}]

    key = str(uuid.uuid4())

    overrides = [
        {
            "key_paths": ["id", "items.id"],
            "override_type": OverrideType.REPLACE_VALUE,
            "override": key,
        },
    ]

    forge = BaseForge("string", overrides)

    with pytest.raises(Exception) as e:
        forge._override_data(data)

    assert str(e.value) == "The key:items must be a list of dicts"


def test_invalid_overrides():
    data = [{"create_date": "", "update_date": ""}]

    overrides = [""]

    forge = BaseForge("string", overrides)

    with pytest.raises(Exception) as e:
        forge._override_data(data)

    assert str(e.value) == "Overrides must be a list[DataForgeConfigOverride]"


def test_invalid_data():
    data = [""]

    overrides = [
        {
            "key_paths": "id",
            "override_type": OverrideType.REPLACE_VALUE,
            "override": "a string",
        },
    ]

    forge = BaseForge("string", overrides)

    with pytest.raises(Exception) as e:
        forge._override_data(data)

    assert str(e.value) == "The provided data must be a list of dictionaries"


def test_key_path_not_found():
    os.environ["DATA_FORGE_SUPPRESS_KEY_PATH_ERRORS"] = "false"

    data = [{"create_date": "", "update_date": ""}]

    overrides = [
        {
            "key_paths": "id",
            "override_type": OverrideType.REPLACE_VALUE,
            "override": "a string",
        },
    ]

    forge = BaseForge("string", overrides)

    with pytest.raises(Exception) as e:
        forge._override_data(data)

    assert str(e.value) == "The key:id does not exist."


def test_invalid_key_path():
    data = [{"create_date": "", "update_date": ""}]
    overrides = [
        {
            "key_paths": 1,
            "override_type": OverrideType.REPLACE_VALUE,
            "override": "a string",
        },
    ]

    forge = BaseForge("string", overrides)

    with pytest.raises(Exception) as e:
        forge._override_data(data)

    assert str(e.value) == "key_paths must be a str or list[str]"


def test_invalid_key_path_list():
    data = [{"create_date": "", "update_date": ""}]

    overrides = [
        {
            "key_paths": [1],
            "override_type": OverrideType.REPLACE_VALUE,
            "override": "a string",
        },
    ]

    forge = BaseForge("string", overrides)

    with pytest.raises(Exception) as e:
        forge._override_data(data)

    assert str(e.value) == "key_paths must be a str or list[str]"


def test_base_key_exists_but_not_dict():
    os.environ["DATA_FORGE_SUPPRESS_KEY_PATH_ERRORS"] = "false"

    data = [{"audit": ""}]

    current_date = datetime.now(UTC).isoformat()
    overrides = [
        {
            "key_paths": "audit.create_date",
            "override_type": OverrideType.REPLACE_VALUE,
            "override": current_date,
        },
    ]

    forge = BaseForge("string", overrides)

    with pytest.raises(Exception) as e:
        forge._override_data(data)

    assert str(e.value) == "The key:audit does not exist or its value is not a dict"


def test_base_key_exists_but_not_dict_suppress():
    data = [{"current_date": "", "audit": ""}]

    current_date = datetime.now(UTC).isoformat()
    overrides = [
        {
            "key_paths": "current_date",
            "override_type": OverrideType.REPLACE_VALUE,
            "override": current_date,
        },
        {
            "key_paths": "audit.create_date",
            "override_type": OverrideType.REPLACE_VALUE,
            "override": current_date,
        },
    ]

    forge = BaseForge("string", overrides)
    update_data = forge._override_data(data)

    assert update_data == [{"current_date": current_date, "audit": ""}]


def test_invalid_format_value():
    data = [{"key_1": 1234}]

    overrides = [
        {
            "key_paths": "key_1",
            "override_type": OverrideType.FORMAT_VALUE,
            "override": ["Avengers"],
        }
    ]

    forge = BaseForge("string", overrides)

    with pytest.raises(Exception) as e:
        forge._override_data(data)

    assert str(e.value) == "The value for key:key_1 must be str for FORMAT_VALUE."


def test_invalid_override_type():
    data = [{"key_1": 1234}]

    overrides = [
        {
            "key_paths": "key_1",
            "override_type": "bad_override_type",
            "override": "",
        }
    ]

    forge = BaseForge("string", overrides)

    with pytest.raises(Exception) as e:
        forge._override_data(data)

    assert str(e.value) == "Unsupported override type - bad_override_type"
