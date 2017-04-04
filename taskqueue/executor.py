import sys
import time
import threading
import uuid
import configparser

from multiprocessing import Process, Queue
from multiprocessing.managers import BaseManager
from threading import Thread
try:
    from queue import Empty
except ImportError:
    from Queue import Empty

class Task():
    def __init__(self, func, *args):
        self.uuid = uuid.uuid4()
        self.func = func
        self.args = args

    def execute(self):
        self.func(*self.args)

class Worker(Thread):
    MILLIS_IN_SECOND = 1000

    def __init__(self, queue, worker_sleep_timeout, logger):
        super(Worker, self).__init__()
        self.queue = queue
        self.worker_sleep_timeout = worker_sleep_timeout
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

            time.sleep(self.worker_sleep_timeout / Worker.MILLIS_IN_SECOND)

        self.logger.info("Stopped worker: "+self.name)
    
    def stop(self):
        self.running = False

class Executor(BaseManager):
    REG_METHOD_NAME = 'get_executor_queue' # the name of the method that is registered to obtain the queue

    def __init__(self, inet_addr, port, authkey, worker_count, worker_sleep_timeout, logger=None):
        super(Executor, self).__init__(address=(inet_addr, port), authkey=authkey)
        self.queue = Queue()
        self.worker_list = []
        self.worker_count = worker_count
        self.worker_sleep_timeout = worker_sleep_timeout

        if logger is None:
            import logging
            logger = logging

        self.logger = logger
        Executor.register(Executor.REG_METHOD_NAME, callable=lambda: self.queue)     

    @staticmethod
    def from_configfile(configfile, logger=None):
        config = ExecutorConfig(configfile)
        return Executor(config.bindaddr, config.port, config.authkey, config.worker_count, config.worker_sleep_timeout, logger)

    def start_server(self):
        self.logger.info("Starting server with "+str(self.worker_count)+" workers and "+str(self.worker_sleep_timeout)+" ms worker timeout")
        
        for i in range(0, self.worker_count):
            w = Worker(self.queue, self.worker_sleep_timeout, self.logger)
            self.worker_list.append(w)
            w.start()

        Executor.get_server(self).serve_forever()

    def stop_server(self): 
        for worker in self.worker_list:
            worker.stop()
            worker.join()
        
        del self.worker_list[:]

class ExecutorConnection(BaseManager):
    def __init__(self, inet_addr, port, authkey):
        super(ExecutorConnection, self).__init__(address=(inet_addr, port), authkey=authkey)
        ExecutorConnection.register(Executor.REG_METHOD_NAME)
        ExecutorConnection.connect(self)
        self.queue = getattr(ExecutorConnection, Executor.REG_METHOD_NAME)(self)

    def call_async(self, func, *args):
        task = Task(func, *args)
        self.queue.put(task)

        return task.uuid

class ExecutorConfig():
    def __init__(self, configfile):
        config = configparser.ConfigParser()
        config.read(configfile)  
        config_params = self.get_config_param(config, 'Executor', "Format error: The ini file needs to contain a section with the name 'Executor'")
        self.authkey = bytes(self.get_config_param(config_params, 'authkey'), 'utf8')
        self.bindaddr = self.get_config_param(config_params, 'bindaddr')
        self.port = int(self.get_config_param(config_params, 'port'))
        self.worker_count = int(self.get_config_param(config_params, 'worker_count'))
        self.worker_sleep_timeout = int(self.get_config_param(config_params, 'worker_sleep_timeout'))

    def get_config_param(self, hash, key, errormsg=None):
        if key in hash:
            return hash[key]
        else:
            if errormsg == None:
                raise Exception("The config parameter "+key+" was not found")

            raise Exception(errormsg) 