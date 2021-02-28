
from boto3 import client
from json import dumps
from src.services.stats import StatsProvider
import traceback
class RemoteQueue(StatsProvider):
    def __init__(self, endPoint: str) -> None:
        StatsProvider.__init__(self, 'queue')
        self.client = client('sqs')
        self.messages = []
        self.endPoint = endPoint
        pass

    def getStats(self):
        error = None
        messageCount= 0
        usedMessageCount = 0
        try:
            response = self.client.get_queue_attributes(
                QueueUrl= self.endPoint,
                AttributeNames=[
                'ApproximateNumberOfMessages',
                'ApproximateNumberOfMessagesNotVisible',
                ]
            )
            if 'Attributes' in response:
                messageCount = int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
                usedMessageCount = int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))
        except:
            error = traceback.format_exc()

        return {
            'error': error,
            'messageCount': messageCount,
            'usedMessageCount': usedMessageCount
        }

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

    def sendMessage(self, messageBoddy: dict):
        body = dumps(messageBoddy)
        self.client.send_message(
            QueueUrl=self.endPoint,
            MessageBody=body,
            DelaySeconds=10,
        )

    def pop(self):
        if len(self.messages):
            return self.messages.pop()