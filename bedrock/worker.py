import json
import boto3

class BedrockWorker:
    def __init__(self, aws_access_key, aws_secret_key, region, model_id):
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        self.model_id = model_id

    def run_model(self, prompt):
        request_payload = {
            "inferenceConfig": {
                "max_new_tokens": 1000
            },
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        payload_str = json.dumps(request_payload)
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=payload_str,
            contentType="application/json",
            accept="application/json"
        )
        response_body = json.loads(response.get("body").read())
        return response_body
