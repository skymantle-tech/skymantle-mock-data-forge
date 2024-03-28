import copy
import os
from collections.abc import Callable
from typing import Final

from boto3 import Session
from skymantle_boto_buddy import cloudformation, ssm

from skymantle_mock_data_forge.models import (
    DataForgeConfigOverride,
    ForgeQuery,
    OverrideType,
)


class BaseForge:
    _operators: Final[dict[str, Callable]] = {
        "StringEquals": lambda value, condition_value: value == condition_value,
        "StringLike": lambda value, condition_value: condition_value in value,
    }

    def __init__(
        self, forge_id: str, overrides: list[DataForgeConfigOverride] | None = None, session: Session = None
    ) -> None:
        self._forge_id: str = forge_id
        self._aws_session = session
        self._overrides = overrides

    def _get_destination_identifier(self, resource_config):
        if resource_config.get("name"):
            value = resource_config["name"]

        elif resource_config.get("ssm"):
            value = ssm.get_parameter(resource_config["ssm"], session=self._aws_session)

        else:
            stack_name = resource_config["stack"]["name"]
            output = resource_config["stack"]["output"]

            outputs = cloudformation.get_stack_outputs(stack_name, session=self._aws_session)
            output_value = outputs.get(output)

            if output_value:
                value = output_value
            else:
                raise Exception(f"Unable to find a resource for stack: {stack_name} and output: {output}")

        return value

    def _get_data_query(self, query: ForgeQuery, data: dict) -> dict:
        if len(query.keys()) == 0:
            raise Exception("Missing operator from query")

        if not set(query.keys()).issubset(self._operators):
            raise Exception(f"Only the following query operators are supported: {list(self._operators.keys())}")

        for condition in query.values():
            if not isinstance(condition, dict):
                raise Exception("The condition for an operator must be a dict.")

        for operator, conditions in query.items():
            for condition_key, condition_value in conditions.items():
                data = self._find_matches(data, operator, condition_key, condition_value)

        return data

    def _find_matches(self, data: dict, operator: str, condition_key: str, condition_value: str) -> dict:
        data = [item for item in data if condition_key in item.get("tags", {})]

        matches = []

        for item in data:
            value = item["tags"][condition_key]

            if isinstance(value, str):
                if self._operators[operator](value, condition_value):
                    matches.append(item)

            elif isinstance(value, list):
                for list_item in value:
                    if not isinstance(list_item, str):
                        raise Exception("Tag values can only be strings or list of strings.")

                    if self._operators[operator](list_item, condition_value):
                        matches.append(item)
                        break
            else:
                raise Exception("Tag values can only be strings or list of strings.")

        return matches

    def _override_data(self, items: list[dict]) -> list[dict]:
        data: list[dict] = [copy.deepcopy(item) for item in items]

        if not self._overrides:
            return data

        if not (isinstance(self._overrides, list) and all(isinstance(item, dict) for item in self._overrides)):
            raise Exception("Overrides must be a list[DataForgeConfigOverride]")

        if not (isinstance(data, list) and all(isinstance(item, dict) for item in data)):
            raise Exception("The provided data must be a list of dictionaries")

        for config_override in self._overrides:
            key_paths = config_override.get("key_paths")

            if isinstance(key_paths, str):
                key_paths = [key_paths]

            elif not (isinstance(key_paths, list) and all(isinstance(item, str) for item in key_paths)):
                raise Exception("key_paths must be a str or list[str]")

            override_type = config_override.get("override_type")
            override = config_override.get("override")

            for key_path in key_paths:
                for item in data:
                    self._update_item(item, key_path, override_type, override)

        return data

    def _update_item(self, item: dict, key_path: str, override_type: OverrideType, override: any):
        try:
            result = self._travel_key_path(item, key_path, override_type, override)

            if result is None:
                return

            key = result[0]
            item_to_update = result[1]

            if key not in item_to_update:
                raise Exception(f"The key:{key} does not exist.")

        except Exception as e:
            suppress_key_path_errors = os.environ.get("DATA_FORGE_SUPPRESS_KEY_PATH_ERRORS", "true")

            if suppress_key_path_errors in ["0", "false", "no", "off"]:
                raise e

            return

        match override_type:
            case OverrideType.REPLACE_VALUE:
                item_to_update[key] = override

            case OverrideType.FORMAT_VALUE:
                value = item_to_update[key]

                if not isinstance(value, str):
                    raise Exception(f"The value for key:{key} must be str for FORMAT_VALUE.")

                item_to_update[key] = value.format(*override)

            case OverrideType.CALL_FUNCTION:
                item_to_update[key] = override(key, item_to_update[key], copy.deepcopy(item))

            case _:
                raise Exception(f"Unsupported override type - {override_type}")

    def _travel_key_path(self, item: dict, key_path: str, override_type: OverrideType, override: any) -> dict:
        keys = key_path.split(".")

        prefix = ""
        temp_item = item

        for key in keys[:-1]:
            prefix += f"{key}."

            temp_item = temp_item.get(key)

            if isinstance(temp_item, list):
                sub_key_path = key_path.removeprefix(prefix)

                # If the item is a list of dictionary. Iterate through the list and finished
                # traversing the key path in each of the items.
                for sub_item in temp_item:
                    if not isinstance(sub_item, dict):
                        raise Exception(f"The key:{key} must be a list of dicts")

                    self._update_item(sub_item, sub_key_path, override_type, override)

                return None

            if not isinstance(temp_item, dict):
                raise Exception(f"The key:{key} does not exist or its value is not a dict")

        return keys[-1], temp_item
