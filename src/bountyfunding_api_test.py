import requests
import os
import signal
import subprocess
import time
from homer import BOUNTYFUNDING_HOME


def setup():
	global bountyfunding_process
	print("Starting BountyFunding API...")
	bountyfunding_process = subprocess.Popen(
		["python", "src/bountyfunding_api.py"], cwd=BOUNTYFUNDING_HOME, 
		preexec_fn=os.setsid
	)
	time.sleep(2)	

def teardown():
	global bountyfunding_process
	print("Stopping BountyFunding API...")
	# Based on http://stackoverflow.com/a/4791612/1106546, won't work on Windows
	os.killpg(bountyfunding_process.pid, signal.SIGKILL)


def test():
	r = requests.get("http://localhost:5000/issue/1")
	assert(r.status_code == 200)
