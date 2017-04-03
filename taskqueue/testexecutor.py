from executor import ExecutorConnection
from sshkm.views.deploy import DeployKeys
from sshkm.models import Setting

id=1
pw=b'g3t1o5t'
con = ExecutorConnection('127.0.0.1', 50000, pw)
master_key_pub = Setting.objects.get(name='MasterKeyPublic')
master_key_priv = Setting.objects.get(name='MasterKeyPrivate')
try:
    passphrase = Setting.objects.get(name='MasterKeyPrivatePassphrase').value
except:
    passphrase = None

for i in range(0, 1):
	print("Accepted task: "+str(con.call_async(DeployKeys, id, master_key_pub, master_key_priv, passphrase)))
