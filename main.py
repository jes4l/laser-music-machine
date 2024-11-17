import subprocess

lazar_process = subprocess.Popen(
    ["python", "lazarDetector.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
)

subprocess.run(["python", "pitch.py"])

stdout, stderr = lazar_process.communicate()
if stdout:
    print(stdout.decode())
if stderr:
    print(stderr.decode())
