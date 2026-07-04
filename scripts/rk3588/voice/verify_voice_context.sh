python3 - <<'PY'
import json, urllib.request, subprocess, time, threading
cmd='source /opt/ros/humble/setup.bash; source /mnt/sdcard/medicine_robot_ws/install/setup.bash; timeout 8 ros2 topic echo /medicine/patient_voice_context --once'
proc=subprocess.Popen(['bash','-lc',cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(1.2)
req=urllib.request.Request('http://127.0.0.1:8081/patient/api/voice/listen', data=json.dumps({'bed':'B-01','duration_sec':300}).encode(), headers={'Content-Type':'application/json'})
print('api=', urllib.request.urlopen(req, timeout=8).read().decode('utf-8')[:220])
out,_=proc.communicate(timeout=10)
print('topic=', out[:1400])
PY
