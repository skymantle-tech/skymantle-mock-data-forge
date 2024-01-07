import copy
import os

from boto3 import Session

from skymantle_mock_data_forge.models import DataForgeConfigOverride, OverideType


class BaseForge:
    def __init__(
        self, forge_id: str, overrides: list[DataForgeConfigOverride] | None = None, session: Session = None
    ) -> None:
        self.forge_id: str = forge_id
        self.aws_session = session
        self.config_overrides = overrides

    def _override_data(self, items: list[dict]) -> list[dict]:
        data: list[dict] = [copy.deepcopy(item) for item in items]

        if not self.config_overrides:
            return data

        if not (
            isinstance(self.config_overrides, list) and all(isinstance(item, dict) for item in self.config_overrides)
        ):
            raise Exception("Overrides must be a list[DataForgeConfigOverride]")

        if not (isinstance(data, list) and all(isinstance(item, dict) for item in data)):
            raise Exception("The provided data must be a list of dictionaries")

        for config_override in self.config_overrides:
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

    def _update_item(self, item: dict, key_path: str, override_type: OverideType, override: any):
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
            case OverideType.REPLACE_VALUE:
                item_to_update[key] = override

            case OverideType.FORMAT_VALUE:
                value = item_to_update[key]

                if not isinstance(value, str):
                    raise Exception(f"The value for key:{key} must be str for FORMAT_VALUE.")

                item_to_update[key] = value.format(*override)

            case OverideType.CALL_FUNCTION:
                item_to_update[key] = override(key, item_to_update[key], copy.deepcopy(item))

            case _:
                raise Exception(f"Unsupported override type - {override_type}")

    def _travel_key_path(self, item: dict, key_path: str, override_type: OverideType, override: any) -> dict:
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
