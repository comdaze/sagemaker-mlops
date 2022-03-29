import json
import uuid
import boto3


# define input content
input_content = {
    "TrainingJobName": "BYOCJob-{}".format(uuid.uuid4().hex),
    "ModelName": "BYOCModel-{}".format(uuid.uuid4().hex),
    "EndpointName": "BYOCEndpoint-{}".format(uuid.uuid4().hex)
}


# invoke step function
sfn_client = boto3.client('stepfunctions')
response = sfn_client.start_execution(
    stateMachineArn='arn:aws-cn:states:cn-northwest-1:456370280007:stateMachine:MyBYOC_11a8778a781d40238d1a7156006ddb60',
    input=str(input_content).replace('\'', '\"')
)
print(response)
print('Done')
