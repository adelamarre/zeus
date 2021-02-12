from PyInquirer import prompt, Separator



class Question():
    def choice(self, message, choices, displayNameKey = 'displayName'):
        c = []
        for key in choices:
            c.append({
                'name': choices[key][displayNameKey],
                'value': key
            })
        options = [{
            'type': 'list',
            'name': 'result',
            'message': message,
            'choices': c,
        }]
        answer = prompt(options)
        return answer.get('result', None)