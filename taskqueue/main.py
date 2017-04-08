if __name__ == "__main__":
	import os
	import sys
	import signal
	import logging
	import django
	import paramiko

	from executor import Executor
	from django import db

	logger = logging.getLogger(__name__)
	#format='%(asctime)s %(message)s', 
	
	abspath = os.path.abspath(os.path.dirname(sys.argv[0]))
	parentpath = os.path.abspath(abspath+"/..")
	sys.path.append(parentpath)
	configfile = abspath+"/executor.ini"
	logging.basicConfig(filename=abspath+'/executor.log', filemode='a', level=logging.INFO)
	executor = Executor.from_configfile(configfile, logger)

	def sigterm_handler(signal, frame):
		logger.info('SIGTERM received! Shutting down workers...')
		executor.stop_server()
		sys.exit(0)

	signal.signal(signal.SIGTERM, sigterm_handler)
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sshkm.settings")
	django.setup()

	logger.info("Task executor startup")
	logger.info("Database connection info: "+str(db.connections.databases))

	#from sshkm.models import Host
	#from sshkm.views.deploy import DeployKeys, DeployConfig
	#hosts = Host.objects.filter(status=Host.STATE_PENDING)
	#deployConfig = DeployConfig()

	#for host in hosts:
	#	executor.addStartupTask(DeployKeys, host, deployConfig)
	#	print(host.id)

	if os.fork():
		sys.exit()

	executor.start_server()