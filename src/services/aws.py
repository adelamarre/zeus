
from boto3 import client

class RemoteQueue:
    def __init__(self, endPoint: str) -> None:
        self.client = client('sqs')
        self.messages = []
        self.endPoint = endPoint
        pass

    
    def provision(self, count=1):
        if len(self.messages) < count:
            if count > 10:
                count = 10
            
            response = self.client.receive_message(
                QueueUrl=self.endPoint,
                MaxNumberOfMessages=count,
                VisibilityTimeout=600,
                WaitTimeSeconds=2,
            )
            if 'Messages' in response:
                newMessages = response['Messages']
                self.messages =  newMessages + self.messages

    def deleteMessage(self, message):
        self.client.delete_message(
                QueueUrl=self.endPoint,
                ReceiptHandle=message['ReceiptHandle']
            )

    def pop(self):
        if len(self.messages):
            return self.messages.pop()