import copy

from boto3 import Session
from skymantle_boto_buddy import cloudformation, dynamodb, ssm

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
        dynamodb_config: DynamoDbForgeConfig,
        session: Session = None,
        overrides: list[DataForgeConfigOverride] | None = None,
    ) -> None:
        super().__init__(forge_id, overrides, session)

        # Get the DynamoDB table name
        if dynamodb_config["table"].get("name"):
            self.table_name: str = dynamodb_config["table"]["name"]
        elif dynamodb_config["table"].get("ssm"):
            self.table_name: str = ssm.get_parameter(dynamodb_config["table"]["ssm"], session=self.aws_session)
        else:
            stack_name = dynamodb_config["table"]["stack"]["name"]
            output = dynamodb_config["table"]["stack"]["output"]

            outputs = cloudformation.get_stack_outputs(stack_name, session=self.aws_session)
            table_name = outputs.get(output)

            if table_name:
                self.table_name: str = table_name
            else:
                raise Exception(f"Unable to find a dynamodb_table for stack: {stack_name} and output: {output}")

        self.primary_key_names: list[str] = dynamodb_config["primary_key_names"].copy()
        self.items: list[DynamoDbItemConfig] = self._override_data(dynamodb_config["items"])

        # Populate the keys list with the keys from all the items.
        # TODO: Validate key conforms to primary_key_names
        self.keys: list[dict[str, str]] = []
        for item in self.items:
            key = {}
            for primary_key_name in self.primary_key_names:
                key[primary_key_name] = item["data"][primary_key_name]

            self.keys.append(key)

    def get_data(self, query: ForgeQuery = None):
        data = [copy.deepcopy(item) for item in self.items]

        if query is None:
            return data

        return self._get_data_query(query, data)

    def add_key(self, key: dict[str, str]) -> None:
        # TODO: Validate key conforms to primary_key_names
        self.keys.append(key)

    def load_data(self) -> None:
        for item in self.items:
            dynamodb.put_item_simplified(self.table_name, item["data"], session=self.aws_session)

    def cleanup_data(self) -> None:
        for key in self.keys:
            dynamodb.delete_item(self.table_name, key, session=self.aws_session)
