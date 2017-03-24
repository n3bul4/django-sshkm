import sys
import time

from multiprocessing import Process, Queue
from multiprocessing.managers import BaseManager

class Task():
    def __init__(self, func, *args):
        self.func = func
        self.args = args

    def execute(self):
        self.func(*self.args)

class Worker(Process):
    def __init__(self, queue):
        self.queue = queue
        super(Worker, self).__init__()
    
    def run(self):
        while True:
            task = self.queue.get()
            msg = str(self.name)+" "+str(task.func)+" called with "+str(len(task.args))+" arguments:"+str(task.args)

            try:
                task.execute()
                msg += " successfully"
            except Exception as e:
                msg += " with exception: "+str(e)+"\n"

            sys.stdout.write(msg)
            time.sleep(100 / 1000)

class Executor(BaseManager):
    def __init__(self, inet_addr, port, authkey, worker_count):
        super().__init__(address=(inet_addr, port), authkey=authkey)
        self.queue = Queue()
        self.worker_list = []
        self.worker_count = worker_count

    def start_server(self):
        for i in range(0, self.worker_count):
            w = Worker(self.queue)
            self.worker_list.append(w)
            w.start()    
        
        Executor.register('get_queue', callable=lambda: self.queue)
        server = Executor.get_server(self)
        server.serve_forever()   

    @staticmethod
    def obtain_queue(inet_addr, port, authkey):
        class QueueManager(BaseManager): pass
        QueueManager.register('get_queue')
        m = QueueManager(address=(inet_addr, port), authkey=authkey)
        m.connect()

        return m.get_queue()
    