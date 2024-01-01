from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from skymantle_mock_data_forge.forge_factory import ForgeFactory


@pytest.fixture()
def mock_dynamodb_forge(mocker: MockerFixture) -> MagicMock:
    mock = mocker.patch("skymantle_mock_data_forge.forge_factory.DynamoDbForge")
    return mock


def test_forge_init(mock_dynamodb_forge):
    data_forge_config = [
        {
            "forge_id": "some_config",
            "dynamodb": {
                "table": {"name": "some_table"},
                "primary_key_names": ["PK"],
                "items": [{"PK": "some_key_1", "Description": "Some description 1"}],
            },
        }
    ]

    ForgeFactory(data_forge_config)

    forge_id = data_forge_config[0]["forge_id"]
    dynamodb = data_forge_config[0]["dynamodb"]
    mock_dynamodb_forge.assert_called_once_with(forge_id, dynamodb, None)


def test_forge_init_invalid_forge_type(mock_dynamodb_forge):
    data_forge_config = [
        {
            "forge_id": "some_config",
            "s3": {},
        }
    ]

    with pytest.raises(Exception) as e:
        ForgeFactory(data_forge_config)

    assert str(e.value) == "Can only have one of the following per config: ['dynamodb']"


def test_load_data(mock_dynamodb_forge):
    data_forge_config = [
        {
            "forge_id": "some_config",
            "dynamodb": {
                "table": {"name": "some_table"},
                "primary_key_names": ["PK"],
                "items": [{"PK": "some_key_1", "Description": "Some description 1"}],
            },
        }
    ]

    forge_factory = ForgeFactory(data_forge_config)

    forge_factory.load_data("some_config")

    mock_dynamodb_forge.return_value.load_data.assert_called_once_with()


def test_load_data_invalid_id(mock_dynamodb_forge):
    data_forge_config = [
        {
            "forge_id": "some_config",
            "dynamodb": {
                "table": {"name": "some_table"},
                "primary_key_names": ["PK"],
                "items": [{"PK": "some_key_1", "Description": "Some description 1"}],
            },
        }
    ]

    forge_factory = ForgeFactory(data_forge_config)

    with pytest.raises(Exception) as e:
        forge_factory.load_data("invalid_config")

    assert str(e.value) == "invalid_config not initialized (some_config)."


def test_cleanup_data(mock_dynamodb_forge):
    data_forge_config = [
        {
            "forge_id": "some_config",
            "dynamodb": {
                "table": {"name": "some_table"},
                "primary_key_names": ["PK"],
                "items": [{"PK": "some_key_1", "Description": "Some description 1"}],
            },
        }
    ]

    forge_factory = ForgeFactory(data_forge_config)

    forge_factory.cleanup_data("some_config")

    mock_dynamodb_forge.return_value.cleanup_data.assert_called_once_with()


def test_cleanup_invalid_id(mock_dynamodb_forge):
    data_forge_config = [
        {
            "forge_id": "some_config",
            "dynamodb": {
                "table": {"name": "some_table"},
                "primary_key_names": ["PK"],
                "items": [{"PK": "some_key_1", "Description": "Some description 1"}],
            },
        }
    ]

    forge_factory = ForgeFactory(data_forge_config)

    with pytest.raises(Exception) as e:
        forge_factory.cleanup_data("invalid_config")

    assert str(e.value) == "invalid_config not initialized (some_config)."


def test_add_key_data(mock_dynamodb_forge):
    data_forge_config = [
        {
            "forge_id": "some_config",
            "dynamodb": {
                "table": {"name": "some_table"},
                "primary_key_names": ["PK"],
                "items": [{"PK": "some_key_1", "Description": "Some description 1"}],
            },
        }
    ]

    forge_factory = ForgeFactory(data_forge_config)

    forge_factory.add_key("some_config", {"PK": "some_key_2"})

    mock_dynamodb_forge.return_value.add_key.assert_called_once_with({"PK": "some_key_2"})


def test_add_key_invalid_id(mock_dynamodb_forge):
    data_forge_config = [
        {
            "forge_id": "some_config",
            "dynamodb": {
                "table": {"name": "some_table"},
                "primary_key_names": ["PK"],
                "items": [{"PK": "some_key_1", "Description": "Some description 1"}],
            },
        }
    ]

    forge_factory = ForgeFactory(data_forge_config)

    with pytest.raises(Exception) as e:
        forge_factory.add_key("invalid_config", {"PK": "some_key_2"})

    assert str(e.value) == "invalid_config not initialized (some_config)."


def test_get_key_data(mock_dynamodb_forge):
    data_forge_config = [
        {
            "forge_id": "some_config",
            "dynamodb": {
                "table": {"name": "some_table"},
                "primary_key_names": ["PK"],
                "items": [{"PK": "some_key_1", "Description": "Some description 1"}],
            },
        }
    ]
    mock_dynamodb_forge.return_value.get_data.return_value = [{"PK": "some_key_1", "Description": "Some description 1"}]

    forge_factory = ForgeFactory(data_forge_config)

    data = forge_factory.get_data("some_config")

    mock_dynamodb_forge.return_value.get_data.assert_called_once_with()
    assert data == [{"PK": "some_key_1", "Description": "Some description 1"}]


def test_get_key_invalid_id(mock_dynamodb_forge):
    data_forge_config = [
        {
            "forge_id": "some_config",
            "dynamodb": {
                "table": {"name": "some_table"},
                "primary_key_names": ["PK"],
                "items": [{"PK": "some_key_1", "Description": "Some description 1"}],
            },
        }
    ]

    forge_factory = ForgeFactory(data_forge_config)

    with pytest.raises(Exception) as e:
        forge_factory.get_data("invalid_config")

    assert str(e.value) == "invalid_config not initialized (some_config)."
