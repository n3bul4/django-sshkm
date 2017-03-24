from executor import Task, Executor
from sshkm.views.deploy import DeployKeys


id=1
pw=b'g3t1o5t'
queue = Executor.obtain_queue('127.0.0.1', 50000, pw)

for i in range(0, 30):
	queue.put(Task(DeployKeys, id))
