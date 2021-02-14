from boto3 import client
from time import sleep
from src.services.console import Console
from sys import stdout
from colorama import Fore, Back, Style
from os import get_terminal_size

console = Console(3, False)

def showStats(data, queueUrl):
    width, height = get_terminal_size()
    console.clearScreen()

    
    separator = '_' * width
    lines = []
    lines.append(Fore.YELLOW + 'AMAZON SQS SERVICE STATS')
    lines.append('\n')
    lines.append(Fore.CYAN + 'Queue: %s:' % queueUrl)
    lines.append(Fore.BLUE + separator)
    lines.append(Fore.WHITE + 'Available messages: %6d' % int(data['ApproximateNumberOfMessages']))
    lines.append(Fore.WHITE + 'Message in use    : %6d' % int(data['ApproximateNumberOfMessagesNotVisible']))
    lines.append(Fore.BLUE + separator)
    index = 1
    for line in lines:
        console.printAt(1, index, line)
        index += 1

    stdout.write('\n')
    stdout.flush()  

client = client('sqs')
queueUrl = 'https://eu-west-3.queue.amazonaws.com/891263387851/ZSPQ'
while True:
    response = client.get_queue_attributes(
        QueueUrl=queueUrl,
        AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
    )
    showStats(response['Attributes'], queueUrl)
    sleep(1)
