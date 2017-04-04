import os, sys
abspath = os.path.abspath(os.path.dirname(sys.argv[0]))
parentpath = os.path.abspath(abspath+"/..")
sys.path.append(parentpath)

from executor import ExecutorConnection
from sshkm.views.deploy import DeployKeys, DeployConfig
from sshkm.models import Setting

id=1
pw=b'g3t1o5t'
con = ExecutorConnection('127.0.0.1', 50000, pw)
deployConfig = DeployConfig()

for i in range(0, 1):
	print("Accepted task: "+str(con.call_async(DeployKeys, id, deployConfig)))
