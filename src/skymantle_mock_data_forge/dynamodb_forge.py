import copy

from boto3 import Session
from skymantle_boto_buddy import cloudformation, dynamodb, ssm

from skymantle_mock_data_forge.models import DynamoDbForgeConfig


class DynamoDbForge:
    def __init__(self, forge_id: str, dynamodb_config: DynamoDbForgeConfig, session: Session = None) -> None:
        self.forge_id: str = forge_id
        self.aws_session = session

        # Get the DynamoDB table name
        if dynamodb_config["table"].get("name"):
            self.table_name: str = dynamodb_config["table"]["name"]
        elif dynamodb_config["table"].get("ssm"):
            self.table_name: str = ssm.get_parameter(dynamodb_config["table"]["ssm"])
        else:
            stack_name = dynamodb_config["table"]["stack"]["name"]
            output = dynamodb_config["table"]["stack"]["output"]

            outputs = cloudformation.get_stack_outputs(stack_name)
            table_name = outputs.get(output)

            if table_name:
                self.table_name: str = table_name
            else:
                raise Exception(f"Unable to find a dynamodb_table for stack: {stack_name} and output: {output}")

        self.primary_key_names: list[str] = dynamodb_config["primary_key_names"].copy()
        self.items: list[dict] = [copy.deepcopy(item) for item in dynamodb_config["items"]]

        # Populate the keys list with the keys from all the items.
        # TODO: Validate key conforms to primary_key_names
        self.keys: list[dict[str, str]] = []
        for item in self.items:
            key = {}
            for primary_key_name in self.primary_key_names:
                key[primary_key_name] = item[primary_key_name]

            self.keys.append(key)

    def get_data(self):
        return [copy.deepcopy(item) for item in self.items]

    def add_key(self, key: dict[str, str]) -> None:
        # TODO: Validate key conforms to primary_key_names
        self.keys.append(key)

    def load_data(self) -> None:
        for item in self.items:
            dynamodb.put_item_simplified(self.table_name, item, session=self.aws_session)

    def cleanup_data(self) -> None:
        for key in self.keys:
            dynamodb.delete_item(self.table_name, key, session=self.aws_session)
