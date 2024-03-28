import copy
from functools import cache

from boto3 import Session
from skymantle_boto_buddy import dynamodb

from skymantle_mock_data_forge.base_forge import BaseForge
from skymantle_mock_data_forge.models import (
    DataForgeConfigOverride,
    DynamoDbForgeConfig,
    DynamoDbItemConfig,
    ForgeQuery,
)


class DynamoDbForge(BaseForge):
    def __init__(
        self,
        forge_id: str,
        config: DynamoDbForgeConfig,
        session: Session = None,
        overrides: list[DataForgeConfigOverride] | None = None,
    ) -> None:
        super().__init__(forge_id, overrides, session)

        self.config = config
        self.primary_key_names: list[str] = config["primary_key_names"].copy()
        self.items: list[DynamoDbItemConfig] = self._override_data(config["items"])

        # Populate the keys list with the keys from all the items.
        # TODO: Validate key conforms to primary_key_names
        self.keys: list[dict[str, str]] = []
        for item in self.items:
            key = {}
            for primary_key_name in self.primary_key_names:
                key[primary_key_name] = item["data"][primary_key_name]

            self.keys.append(key)

    @cache
    def _get_table_name(self):
        resource_config = self.config["table"]
        return self._get_destination_identifier(resource_config)

    def get_data(self, *, query: ForgeQuery, return_tags: bool):
        data = [copy.deepcopy(item) for item in self.items]

        if query is not None:
            data = self._get_data_query(query, data)

        if not return_tags:
            data = [item["data"] for item in data]

        return data

    def add_key(self, key: dict[str, str]) -> None:
        # TODO: Validate key conforms to primary_key_names
        self.keys.append(key)

    def load_data(self) -> None:
        for item in self.items:
            dynamodb.put_item_simplified(self._get_table_name(), item["data"], session=self.aws_session)

    def cleanup_data(self) -> None:
        for key in self.keys:
            dynamodb.delete_item(self._get_table_name(), key, session=self.aws_session)
