import queue

class Application:
    def __init__(self):
        self.queue = queue.Queue()

    def enqueue(self, item):
        self.queue.put(item)

    def dequeue(self):
        return self.queue.get()