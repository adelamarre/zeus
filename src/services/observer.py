





class Observer:
    def notify(self, eventName: str, target, data = {}):
        pass

class Subject:
    def __init__(self) -> None:
        self.observers = {}

    def attach(self, events: list, observer: Observer) -> None:
        for eventName in events:
            if not eventName in self.observers:
                self.observers[eventName] = []
            self.observers[eventName].append(observer)
    
    def trigger(self, eventName: str, data={}):
        if eventName in self.observers:
            for observer in self.observers[eventName]:
                observer.notify(eventName, self, data)

