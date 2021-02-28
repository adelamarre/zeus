from PyInquirer import prompt, Separator
from validators import url as urlValidator
import hashlib 

class Question():
    def yesNo(message, default: bool =True):
        answer = prompt([{
            'type': 'confirm',
            'name': 'result',
            'message': message,
            'default': default

        }])
        return answer.get('result', None)

    def list(questions):
        answer = prompt(questions)
        return answer

    def choice(self, message, choices, displayNameKey = 'displayName'):
        c = []
        for key in choices:
            c.append({
                'name': choices[key][displayNameKey],
                'value': key,
                'disabled': choices[key].get('disabled', None)
            })
        options = [{
            'type': 'list',
            'name': 'result',
            'message': message,
            'choices': c,
        }]
        answer = prompt(options)
        return answer.get('result', None)
    
    def validateUrl(data):
        return True if urlValidator(data) else 'Sorry, bad url...'

    def when(key):
        def _when(data):
            if key in data:
                return bool(data[key])
            return False
        return _when

    def filterMd5(secret):
        if len(secret):
            return hashlib.md5(str.encode(secret)).hexdigest()
        return None

    def validateInteger(number):
        try:
            value = int(number)
            if value > 0: return True
        except:
            pass
        return 'Please give me a number other than zero...'
    
    def validateFloat(number):
        try:
            value = float(number)
            if value > 0.0: return True
        except:
            pass
        return 'Please give me a number other than zero...'

    def validateString(name):
        min = 2
        if len(str(name)) < min:
            return 'The name must %d letters minimum...' % min
        return True