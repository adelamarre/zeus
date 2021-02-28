from boto3 import client
from time import sleep
from src.services.console import Console
from sys import stdout, argv
from colorama import Fore, Back, Style
from os import get_terminal_size
from traceback import format_exc
from src.services.stats import Stats
console = Console(3, False)

def showStats(data, queueUrl, stats: Stats):
    width, height = get_terminal_size()
        
    separator = '_' * width
    lines = []
    lines.append(Fore.YELLOW + 'AMAZON SQS SERVICE STATS')
    lines.append('\n')
    lines = lines + stats.getConsoleLines(width)
    lines.append(Fore.CYAN + 'Queue: %s:' % queueUrl)
    lines.append(Fore.BLUE + separator)
    lines.append(Fore.WHITE + 'Available messages: %6d' % int(data['ApproximateNumberOfMessages']))
    lines.append(Fore.WHITE + 'Message in use    : %6d' % int(data['ApproximateNumberOfMessagesNotVisible']))
    lines.append(Fore.BLUE + separator)
    console.clearScreen()
    index = 1
    for line in lines:
        console.printAt(1, index, line)
        index += 1

    
    stdout.flush()  


if __name__ == '__main__':
    for arg in argv:
        showInfo = (arg == '--info')
    client = client('sqs')
    stats = Stats()
    queueUrl = 'https://eu-west-3.queue.amazonaws.com/891263387851/ZSPQ'
    while True:
        try:
            response = client.get_queue_attributes(
                QueueUrl=queueUrl,
                AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
            )
            if showInfo:
                showStats(response['Attributes'], queueUrl, stats)
            sleep(1)
        except KeyboardInterrupt:
            break
        except:
            print(format_exc())
            break
