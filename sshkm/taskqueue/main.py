if __name__ == "__main__":
	import os
	import django
	from executor import Executor
	from django import db

	os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sshkm.settings")
	django.setup()
	print ("Database connection info: ", db.connections.databases)
	pw=b'g3t1o5t'
	executor = Executor('127.0.0.1', 50000, pw, 3)
	executor.start_server()