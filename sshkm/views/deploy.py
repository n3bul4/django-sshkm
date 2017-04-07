from django.utils import timezone
import paramiko

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

from sshkm.models import Host, Osuser, Key, KeyGroup, Permission, Setting
import logging

class DeployConfig():
    STATE_PENDING = 0
    STATE_SUCCESS = 1
    STATE_FAILURE = 2
    STATE_NOTHING_TO_DEPLOY = 3
    GLOBAL_SUPER_USER = "root"

    def __init__(self):
        self.master_key_pub = Setting.objects.get(name='MasterKeyPublic')
        self.master_key_priv = Setting.objects.get(name='MasterKeyPrivate')
            
        try:
            self.passphrase = Setting.objects.get(name='MasterKeyPrivatePassphrase').value
        except:
            self.passphrase = None

        try:
            self.globalsuperuser = Setting.objects.get(name='SuperUser').value

            if not self.globalsuperuser or self.globalsuperuser == "":
                self.globalsuperuser = DeployConfig.GLOBAL_SUPER_USER
        except:
            self.globalsuperuser = DeployConfig.GLOBAL_SUPER_USER
            
        

    #sadly RSAKey is not pickelable, so we can't create it in the constructor. 
    #For now we create it on the fly through this method for every damn host deploy (***sigh***)
    def getPrivKey(self):
        pkeyFileHandle = StringIO(self.master_key_priv.value)
        privKey = paramiko.RSAKey.from_private_key(pkeyFileHandle, password=self.passphrase)
        pkeyFileHandle.close()

        return privKey


class NothingToDeployException(Exception):
    pass


class SSHConnection():
    def __init__(self):
        self.client = paramiko.SSHClient()
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self, host, superuser, private_key, timeout):
        self.client.connect(host, username=superuser, pkey=private_key, timeout=timeout)

    def close(self):
        self.client.close()

    def copyKey(self, osuser, home, keyfile):
        authKeyFile = home + "/.ssh/authorized_keys"
        sshDir = home + '/.ssh'
        self.client.exec_command('mkdir -p ' + sshDir)
        self.client.exec_command('chown ' + osuser + ' ' + sshDir)
        self.stdin, stdout, stderr = self.client.exec_command('echo "' + keyfile + '" > ' + authKeyFile)
        self.client.exec_command('chown ' + osuser + ' ' + authKeyFile)
        self.client.exec_command('chmod 600 ' + authKeyFile)

class OsUserInfo():
    def __init__(self, osuser):
        self.osuser = osuser
        self.pubKeys = []

        if osuser.home is None or osuser.home == "":
            if osuser.name == 'root':
                self.home = '/root'
            else:
                self.home = '/home/' + osuser.name
        else:
            self.home = osuser.home

def getOsuserKeyMap(host_id):
    osuserMap = {}

    permissions = Permission.objects.filter(host_id=host_id).order_by('osuser_id')

    for permission in permissions:
        keygroups = KeyGroup.objects.filter(group_id=permission.group_id).order_by('key_id')

        for keygroup in keygroups:
            key = Key.objects.get(id=keygroup.key_id)
            osuser = Osuser.objects.get(id=permission.osuser_id)

            if key.publickey is not None and key.publickey != "":
                osuserInfo = None

                if osuser.id in osuserMap:
                    osuserInfo = osuserMap[osuser.id]
                else:
                    osuserInfo = OsUserInfo(osuser)
                    osuserMap[osuser.id] = osuserInfo

                osuserInfo.pubKeys.append(key.publickey)
        
    return osuserMap

def DeployKeys(host_id, deployConfig):
    osuserMap = getOsuserKeyMap(host_id)
    host = Host.objects.get(id=host_id)

    if len(osuserMap) == 0:
        # nothing to deploy
        host.saveStatus(DeployConfig.STATE_NOTHING_TO_DEPLOY)
        raise NothingToDeployException()
    else:
        if host.superuser and host.superuser != "":
            superuser = host.superuser
        else:
            superuser = deployConfig.globalsuperuser

        sshCon = SSHConnection()

        try:
            sshCon.connect(host.name, superuser, deployConfig.getPrivKey(), 5)

            for id, osuserInfo in osuserMap.items():
                keyFile = ''

                for pubKey in osuserInfo.pubKeys:
                    keyFile += pubKey + '\n'

                if osuserInfo.osuser.name == superuser:
                    keyFile = deployConfig.master_key_pub.value + '\n' + keyFile
                
                sshCon.copyKey(osuserInfo.osuser.name, osuserInfo.home, keyFile)

            host.saveStatus(DeployConfig.STATE_SUCCESS)
        except Exception as e:
            host.saveStatus(DeployConfig.STATE_FAILURE)
            raise
        finally:
            sshCon.close()
