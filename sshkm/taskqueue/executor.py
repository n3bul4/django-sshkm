import sys
import time
import threading
import uuid

from multiprocessing import Process, Queue
from queue import Empty
from multiprocessing.managers import BaseManager
from threading import Thread

class Task():
    def __init__(self, func, *args):
        self.uuid = uuid.uuid4()
        self.func = func
        self.args = args

    def execute(self):
        self.func(*self.args)

class Worker(Thread):
    def __init__(self, queue, logger):
        super(Worker, self).__init__(daemon=True)
        self.queue = queue
        self.logger = logger
        self.running = True

    def run(self):
        self.logger.info("Starting worker: "+self.name+" "+str(threading.current_thread()))

        while self.running:
            try:
                task = self.queue.get(timeout=3)
                msg = str(task.uuid)+" "+str(self.name)+" "+str(task.func)+" called with "+str(len(task.args))+" arguments:"+str(task.args)   

                try: 
                    task.execute()
                    self.logger.info(msg)
                except Exception as e:
                    self.logger.error(msg+" "+str(e)+";"+"Exception class: "+str(e.__class__))
            except Empty:
                pass

            time.sleep(100 / 1000)

        self.logger.info("Stopped worker: "+self.name)
    
    def stop(self):
        self.running = False

class Executor(BaseManager):
    REG_METHOD_NAME = 'get_executor_queue' # the name of the method that is registered to obtain the queue

    def __init__(self, inet_addr, port, authkey, worker_count, logger=None):
        super().__init__(address=(inet_addr, port), authkey=authkey)
        self.queue = Queue()
        self.worker_list = []
        self.worker_count = worker_count

        if logger is None:
            import logging
            logger = logging

        self.logger = logger
        Executor.register(Executor.REG_METHOD_NAME, callable=lambda: self.queue)
        Executor.register('Listener', Test)     

    def start_server(self):
        self.logger.info("Starting server with "+str(self.worker_count)+" workers")
        
        for i in range(0, self.worker_count):
            w = Worker(self.queue, self.logger)
            self.worker_list.append(w)
            w.start()

        Executor.get_server(self).serve_forever()

    def stop_server(self): 
        for worker in self.worker_list:
            worker.stop()
            worker.join()
        
        del self.worker_list[:]

class Test():
    def test():
        print("Test")

class ExecutorConnection(BaseManager):
    def __init__(self, inet_addr, port, authkey):
        super().__init__(address=(inet_addr, port), authkey=authkey)
        ExecutorConnection.register(Executor.REG_METHOD_NAME)
        Executor.register('Listener', Test)  
        ExecutorConnection.connect(self)
        self.queue = getattr(ExecutorConnection, Executor.REG_METHOD_NAME)(self)

    def call_async(self, func, *args):
        task = Task(func, *args)
        self.queue.put(task)

        return task.uuid