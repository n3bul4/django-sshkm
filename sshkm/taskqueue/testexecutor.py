from executor import ExecutorConnection
from sshkm.views.deploy import DeployKeys


id=1
pw=b'g3t1o5t'
con = ExecutorConnection('127.0.0.1', 50000, pw)

for i in range(0, 1000):
	print("Accepted task: "+str(con.call_async(DeployKeys, id)))
