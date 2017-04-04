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
	logging.basicConfig(filename='executor.log', filemode='a', level=logging.INFO)
	pw=b'g3t1o5t'
	executor = Executor.from_configfile('executor.ini', logger)

	def sigterm_handler(signal, frame):
		logger.info('SIGTERM received! Shutting down workers...')
		executor.stop_server()
		sys.exit(0)

	signal.signal(signal.SIGTERM, sigterm_handler)
	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sshkm.settings")
	django.setup()

	logger.info("Task executor startup")
	logger.info("Database connection info: "+str(db.connections.databases))
	
	
	if os.fork():
		sys.exit()

	
	executor.start_server()