# ============================================================
# robot_voice_6.py — Dual Robotic Arm System
# Coordinated Pick-and-Place Middleware
# University of Kent — EENG6010
#
# Voice engine: macOS Samantha TTS exclusively
# (No MP3 files required — fully offline)
#
# Roles:
#   • Serial handshake and high-frequency telemetry parsing
#   • Forward-kinematics computation and trajectory logging
#   • Samantha TTS audio synchronised to physical arm phases
#   • Flask web server serving /data, /trajectory, /metrics
#
# Usage:
#   python robot_voice_6.py
#   >> run     (start coordinated pick-and-place sequence)
#   >> exit    (shut down)
# ============================================================

import serial
import time
import subprocess
import os
import threading
import math
import logging
from collections import deque
from flask import Flask, render_template, jsonify

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# ============================================================
# CONFIGURATION — update MAC_PORT to match your Arduino port
# ============================================================
HOST               = '127.0.0.1'
PORT               = 5001
DASHBOARD_TEMPLATE = 'dashboard_4.html'
_TEMPLATES_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  '..', 'templates')

MAC_PORT  = '/dev/cu.usbmodem1051DB36C9142'   # Update for your system
BAUD_RATE = 115200

# ============================================================
# SPEECH DICTIONARY (Samantha TTS — calibrated velocity)
# ============================================================
text_fallback = {
    "System Ready":          "FRIDAY online. Systems primed.",
    "Homing both arms":      "Returning both arms to home position.",
    "Mission complete":      "All objectives completed. Systems nominal.",
    "Both arms approaching": "Initiating synchronized approach. Both arms descending to target.",
    "Both arms grabbing":    "Synchronized grip engaged. Both grippers closing.",
    "Both arms lifting":     "Bilateral lift initiated. Object rising.",
    "Holding position":      "Object secured at lift height. Holding.",
    "Both arms placing":     "Controlled descent. Both arms lowering simultaneously.",
    "Both arms releasing":   "Releasing payload. Both grippers opening.",
}

# ============================================================
# SHARED STATE
# ============================================================
servo_angles   = {str(i): 90 for i in range(16)}
current_action = "Initializing..."
speak_lock     = threading.Lock()
active         = True
cmd_queue      = deque()

hw_status = {"serial_ok": False, "arduino_ok": False, "error_msg": None}

# ============================================================
# TRAJECTORY / METRICS
# ============================================================
MAX_HISTORY = 5000

HOME = {
    0:  85, 1:  90, 2:  91, 3:  96, 4:  90, 5:  90,
    10: 93, 11: 90, 12: 90, 13: 92, 14: 90, 15: 90,
}
LEFT_PINS  = [0, 1, 2, 3, 4, 5]
RIGHT_PINS = [10, 11, 12, 13, 14, 15]

mission_start   = None
mission_started = False
trajectory_lock = threading.Lock()
trajectory = {
    "t":             deque(maxlen=MAX_HISTORY),
    "left_gripper":  deque(maxlen=MAX_HISTORY),
    "right_gripper": deque(maxlen=MAX_HISTORY),
    "actions":       [],
}

# ============================================================
# FORWARD KINEMATICS
# ============================================================
def _normalize(v):
    L = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
    if L < 1e-10: return (0.0, 1.0, 0.0)
    return (v[0]/L, v[1]/L, v[2]/L)
def _vec_add(a, b):    return (a[0]+b[0], a[1]+b[1], a[2]+b[2])
def _vec_scale(v, s):  return (v[0]*s, v[1]*s, v[2]*s)
def _servo_angle(pin): return int(servo_angles.get(str(pin), HOME[pin]))

def compute_gripper_position(pins, offset_x):
    p        = pins
    base_rad = ((_servo_angle(p[0]) - HOME[p[0]]) / 90.0) * (math.pi * 0.5)
    sag_sign = -1.0 if p[0] == 0 else 1.0
    if p[0] == 0: base_rad *= -1.0

    shoulder_tilt = ((_servo_angle(p[1]) - HOME[p[1]]) / 90.0) * math.pi * 0.75 * sag_sign
    elbow_tilt    = -(((_servo_angle(p[2]) - HOME[p[2]]) / 90.0) * math.pi * 0.65) * sag_sign
    wrist_tilt    = -(((_servo_angle(p[4]) - HOME[p[4]]) / 90.0) * math.pi * 0.30) * sag_sign

    base_top     = (offset_x, 0.6, 0.0)
    shoulder_dir = _normalize((math.sin(base_rad)*math.sin(shoulder_tilt),
                                math.cos(shoulder_tilt),
                                math.cos(base_rad)*math.sin(shoulder_tilt)))
    elbow_pos    = _vec_add(base_top, _vec_scale(shoulder_dir, 2.0))

    cumul_tilt   = shoulder_tilt + elbow_tilt
    elbow_dir    = _normalize((math.sin(base_rad)*math.sin(cumul_tilt),
                                math.cos(cumul_tilt),
                                math.cos(base_rad)*math.sin(cumul_tilt)))
    wrist_pos    = _vec_add(elbow_pos, _vec_scale(elbow_dir, 1.6))

    wrist_cum    = cumul_tilt + wrist_tilt
    wrist_dir    = _normalize((math.sin(base_rad)*math.sin(wrist_cum),
                                math.cos(wrist_cum),
                                math.cos(base_rad)*math.sin(wrist_cum)))
    return _vec_add(wrist_pos, _vec_scale(wrist_dir, 0.8))

def update_trajectory():
    if not mission_started or mission_start is None: return
    t_rel = time.time() - mission_start
    with trajectory_lock:
        trajectory["t"].append(t_rel)
        trajectory["left_gripper"].append(list(compute_gripper_position(LEFT_PINS,  -4.0)))
        trajectory["right_gripper"].append(list(compute_gripper_position(RIGHT_PINS,  4.0)))

def _distance_from_base(grip_xyz, origin_x):
    dx = grip_xyz[0] - origin_x
    return math.sqrt(dx*dx + grip_xyz[1]*grip_xyz[1] + grip_xyz[2]*grip_xyz[2])

def _inter_gripper(l, r):
    return math.sqrt(sum((l[i]-r[i])**2 for i in range(3)))

# ============================================================
# FLASK APP
# ============================================================
app = Flask(__name__, template_folder=_TEMPLATES_DIR)

@app.route('/')
def index(): return render_template(DASHBOARD_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'mission_started': mission_started,
                    'serial_ok': hw_status['serial_ok'], 'arduino_ok': hw_status['arduino_ok']})

@app.route('/data')
def data(): return jsonify({'angles': servo_angles, 'action': current_action})

@app.route('/trajectory')
def trajectory_endpoint():
    with trajectory_lock:
        return jsonify({'mission_start': mission_start, 'mission_started': mission_started,
                        't': list(trajectory['t']),
                        'left_gripper': list(trajectory['left_gripper']),
                        'right_gripper': list(trajectory['right_gripper']),
                        'actions': list(trajectory['actions'])})

@app.route('/metrics')
def metrics_endpoint():
    with trajectory_lock:
        ts        = list(trajectory['t'])
        left_pts  = list(trajectory['left_gripper'])
        right_pts = list(trajectory['right_gripper'])
        n, ms, started = len(ts), mission_start, mission_started

    elapsed = (time.time() - ms) if ms and started else 0.0
    dl, dr, di = [], [], []
    for i in range(n):
        dl.append(_distance_from_base(left_pts[i], -4.0))
        dr.append(_distance_from_base(right_pts[i], 4.0))
        di.append(_inter_gripper(left_pts[i], right_pts[i]))

    def _mm(v): return {'min': min(v), 'max': max(v), 'current': v[-1]} if v else \
                        {'min': None, 'max': None, 'current': None}
    return jsonify({'mission_start': ms, 'mission_started': started, 'elapsed_s': elapsed,
                    'samples': n, 'distance_left': _mm(dl), 'distance_right': _mm(dr),
                    'inter_gripper': _mm(di)})

# ============================================================
# AUDIO ENGINE (Samantha TTS only)
# ============================================================
def speak(text=None, blocking=False):
    def _speak():
        with speak_lock:
            if text:
                subprocess.run(['say', '-v', 'Samantha', '-r', '180', text])
    t = threading.Thread(target=_speak, daemon=True)
    t.start()
    if blocking: t.join()
    return t

# ============================================================
# SERIAL COMMUNICATION THREAD
# ============================================================
def serial_thread():
    global current_action, active, servo_angles, mission_start, mission_started

    try:
        ser = serial.Serial(MAC_PORT, BAUD_RATE, timeout=1)
    except Exception as e:
        print(f"\nCRITICAL: Cannot open port {MAC_PORT}. Close Arduino IDE Serial Monitor.")
        os._exit(1)

    hw_status['serial_ok'] = True
    time.sleep(2)
    ser.write(b"k")  # Send knock

    # Handshake
    ready = False
    while not ready:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("Servo:"):
                parts = line.replace("Servo:", "").split(",")
                if len(parts) == 2:
                    try: servo_angles[parts[0].strip()] = int(parts[1].strip())
                    except: pass
                continue
            if "System Ready" in line:
                hw_status['arduino_ok'] = True
                current_action = "System Ready"
                speak(text_fallback["System Ready"], blocking=True)
                ready = True
        time.sleep(0.1)

    print("\n✅ Handshake complete. Waiting for 'run' command...\n")

    # Persistent execution loop
    while active:
        if cmd_queue:
            cmd = cmd_queue.popleft()
            if cmd == "run":
                ser.write(b"test\n")
                mission_start   = time.time()
                mission_started = True
                with trajectory_lock:
                    trajectory['t'].clear()
                    trajectory['left_gripper'].clear()
                    trajectory['right_gripper'].clear()
                    trajectory['actions'].clear()

        # Drain entire buffer (serial buffer drain fix — prevents audio lag)
        while ser.in_waiting > 0:
            try: line = ser.readline().decode('utf-8', errors='ignore').strip()
            except: continue
            if not line: continue

            if line.startswith("Servo:"):
                parts = line.replace("Servo:", "").split(",")
                if len(parts) == 2:
                    try: servo_angles[parts[0].strip()] = int(parts[1].strip())
                    except: pass
                    else: update_trajectory()

            elif line.startswith("Action:"):
                message        = line.replace("Action:", "").strip()
                current_action = message
                print(f"ACTION: {message}", flush=True)

                if mission_started and mission_start is not None:
                    with trajectory_lock:
                        trajectory['actions'].append(
                            {'t': time.time() - mission_start, 'message': message})

                t = speak(text_fallback.get(message, message), blocking=False)

                if "mission complete" in message.lower():
                    t.join()
                    speak("Synchronized pick protocol concluded. Both systems returning to standby.",
                          blocking=True)
                    print("\n--- MISSION COMPLETE ---")
                    print(">> Type 'run' to restart, or 'exit' to quit.\n")

        time.sleep(0.005)

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    dash_url = f'http://{HOST}:{PORT}/'
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  DUAL ROBOTIC ARM — SYNCHRONIZED PICK MODE")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Dashboard : {dash_url}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    threading.Thread(target=serial_thread, daemon=True).start()
    threading.Thread(target=lambda: app.run(host=HOST, port=PORT,
                                            debug=False, use_reloader=False),
                     daemon=True).start()
    try:
        while True:
            user_input = input(">> ").strip().lower()
            if user_input == 'run':
                cmd_queue.append('run')
            elif user_input == 'exit':
                print("Shutting down system...")
                os._exit(0)
    except KeyboardInterrupt:
        os._exit(0)
