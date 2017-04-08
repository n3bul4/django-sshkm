from __future__ import absolute_import, unicode_literals
from celery import shared_task

from sshkm.views.deploy import DeployKeys, DeployKeysCelery, DeployConfig
from taskqueue.executor import ExecutorConnection

class Provider():
	def connect(self):
		pass

class RemoteTaskQueueProvider(Provider):
	def __init__(self, host, port, pw):
		self.host = host
		self.port = port
		self.pw = pw
	
	def connect(self):
		self.provider = ExecutorConnection(self.host, self.port, self.pw)

	def call_async(self, hostModel, deployConfig):
		self.provider.call_async(DeployKeys, hostModel, deployConfig)

	def getName(self):
		return "Remote TaskQueue"

@shared_task
def ScheduleDeployKeys(hostId):
	DeployKeysCelery(hostId, DeployConfig())

class CeleryProvider(Provider):
	def call_async(self, hostModel, deployConfig):
		ScheduleDeployKeys.apply_async(args=[hostModel.id])

	def getName(self):
		return "Celery"