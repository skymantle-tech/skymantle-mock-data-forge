import copy

from boto3 import Session
from skymantle_boto_buddy import cloudformation, s3, ssm

from skymantle_mock_data_forge.models import S3ForgeConfig, S3ObjectConfig


class S3Forge:
    def __init__(self, forge_id: str, s3_config: S3ForgeConfig, session: Session = None) -> None:
        self.forge_id: str = forge_id
        self.aws_session = session

        # Get the S3 bucket name
        if s3_config["bucket"].get("name"):
            self.bucket_name: str = s3_config["bucket"]["name"]
        elif s3_config["bucket"].get("ssm"):
            self.bucket_name: str = ssm.get_parameter(s3_config["bucket"]["ssm"], session=self.aws_session)
        else:
            stack_name = s3_config["bucket"]["stack"]["name"]
            output = s3_config["bucket"]["stack"]["output"]

            outputs = cloudformation.get_stack_outputs(stack_name, session=self.aws_session)
            bucket_name = outputs.get(output)

            if bucket_name:
                self.bucket_name: str = bucket_name
            else:
                raise Exception(f"Unable to find a bucket_name for stack: {stack_name} and output: {output}")

        self.s3_objects: list[S3ObjectConfig] = [copy.deepcopy(s3_object) for s3_object in s3_config["s3_object"]]
        self.keys: list[str] = [s3_object["key"] for s3_object in s3_config["s3_object"]]

    def get_data(self):
        return [copy.deepcopy(s3_object) for s3_object in self.s3_objects]

    def add_key(self, key: str) -> None:
        self.keys.append(key)

    def load_data(self) -> None:
        for s3_object in self.s3_objects:
            s3.put_object(self.bucket_name, s3_object["key"], s3_object["data"]["text"], session=self.aws_session)

    def cleanup_data(self) -> None:
        s3.delete_objects_simplified(self.bucket_name, self.keys, session=self.aws_session)
