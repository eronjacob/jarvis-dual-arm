# ============================================================
# robot_voice_5.py — J.A.R.V.I.S. Dual Robotic Arm System
# Handover Task Middleware
# University of Kent — EENG6010
#
# Roles:
#   • Serial handshake and telemetry parsing
#   • Forward-kinematics computation and trajectory logging
#   • Audio engine (ElevenLabs MP3 with macOS 'say' fallback)
#   • Flask web server serving /data, /trajectory, /metrics
#
# Usage:
#   python robot_voice_5.py
#   >> run     (start handover sequence)
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

# Suppress Flask/Werkzeug HTTP request log waterfall
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# ============================================================
# CONFIGURATION — update MAC_PORT to match your Arduino port
# ============================================================
HOST               = '127.0.0.1'
PORT               = 5001
DASHBOARD_TEMPLATE = 'dashboard_3.html'
_TEMPLATES_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  '..', 'templates')

MAC_PORT  = '/dev/cu.usbmodem1051DB36C9142'   # Update for your system
BAUD_RATE = 115200
AUDIO_DIR = os.path.expanduser('~/Desktop/JARVIS_Audio')

# ============================================================
# AUDIO FILE MAP (ElevenLabs pre-generated MP3s)
# Falls back to macOS 'say' if files not found
# ============================================================
audio_map = {
    "System Ready":                  "system_ready.mp3",
    "Left arm picking":              "left_arm_picking.mp3",
    "Centering mass":                "centering_mass.mp3",
    "Rotating to handover":          "rotating_to_handover.mp3",
    "Extending left arm":            "extending_left_arm.mp3",
    "Right arm receiving":           "right_arm_receiving.mp3",
    "Right arm grabbing":            "right_arm_grabbing.mp3",
    "Left arm release":              "left_arm_release.mp3",
    "Right arm moving to drop zone": "drop_zone.mp3",
    "Dropping object":               "dropping_object.mp3",
    "Homing both arms":              "homing_both_arms.mp3",
    "Mission complete":              "mission_complete.mp3",
}

text_fallback = {
    "System Ready":                  "JARVIS online. Good evening sir. Dual robotic handover sequence primed.",
    "Left arm picking":              "Initiating left arm retrieval sequence.",
    "Centering mass":                "Centering payload. Mass distribution nominal.",
    "Rotating to handover":          "Rotating to handover coordinates. Stand by.",
    "Extending left arm":            "Extending left arm to transfer position.",
    "Right arm receiving":           "Right arm moving to intercept. Tracking payload.",
    "Right arm grabbing":            "Payload secured. Grip confirmed.",
    "Left arm release":              "Left arm disengaging. Transfer complete, sir.",
    "Right arm moving to drop zone": "Navigating to drop zone. Calculating optimal placement.",
    "Dropping object":               "Releasing payload. Placement confirmed.",
    "Homing both arms":              "Returning both arms to home position.",
    "Mission complete":              "All objectives completed. Systems nominal, sir.",
}

# ============================================================
# SHARED STATE
# ============================================================
servo_angles   = {str(i): 90 for i in range(16)}
current_action = "Initializing..."
speak_lock     = threading.Lock()
active         = True
cmd_queue      = deque()

hw_status = {
    "serial_ok":  False,
    "audio_ok":   False,
    "arduino_ok": False,
    "error_msg":  None,
}

# ============================================================
# TRAJECTORY / METRICS
# ============================================================
MAX_HISTORY = 5000

HOME = {
    0: 85, 1: 90, 2: 91, 3: 96, 4: 90, 5: 90,
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
# FORWARD KINEMATICS (vector-geometric approximation)
# Mirrors the JavaScript implementation in dashboard_3.html
# ============================================================
def _vec_len(v):   return math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
def _normalize(v):
    L = _vec_len(v)
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

    cumul_tilt  = shoulder_tilt + elbow_tilt
    elbow_dir   = _normalize((math.sin(base_rad)*math.sin(cumul_tilt),
                               math.cos(cumul_tilt),
                               math.cos(base_rad)*math.sin(cumul_tilt)))
    wrist_pos   = _vec_add(elbow_pos, _vec_scale(elbow_dir, 1.6))

    wrist_cum   = cumul_tilt + wrist_tilt
    wrist_dir   = _normalize((math.sin(base_rad)*math.sin(wrist_cum),
                               math.cos(wrist_cum),
                               math.cos(base_rad)*math.sin(wrist_cum)))
    return _vec_add(wrist_pos, _vec_scale(wrist_dir, 0.8))

def update_trajectory():
    if not mission_started or mission_start is None: return
    t_rel = time.time() - mission_start
    with trajectory_lock:
        trajectory["t"].append(t_rel)
        trajectory["left_gripper"].append(list(compute_gripper_position(LEFT_PINS, -4.0)))
        trajectory["right_gripper"].append(list(compute_gripper_position(RIGHT_PINS, 4.0)))

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
# AUDIO ENGINE
# ============================================================
def check_audio_files():
    if not os.path.exists(AUDIO_DIR):
        print(f"WARNING: Audio folder not found: {AUDIO_DIR}")
        hw_status['audio_ok'] = False
        return False
    hw_status['audio_ok'] = True
    return True

def speak(filename=None, fallback_text=None, blocking=False):
    def _speak():
        with speak_lock:
            played = False
            if filename and os.path.exists(os.path.join(AUDIO_DIR, filename)):
                subprocess.run(['afplay', os.path.join(AUDIO_DIR, filename)])
                played = True
            if not played and fallback_text:
                subprocess.run(['say', '-v', 'Daniel', '-r', '135', fallback_text])
    t = threading.Thread(target=_speak, daemon=True)
    t.start()
    if blocking: t.join()
    return t

# ============================================================
# SERIAL COMMUNICATION THREAD
# ============================================================
def serial_thread():
    global current_action, active, servo_angles, mission_start, mission_started
    check_audio_files()

    print(f"Attempting to open {MAC_PORT} at {BAUD_RATE} baud...")
    try:
        ser = serial.Serial(MAC_PORT, BAUD_RATE, timeout=2)
    except Exception as e:
        print(f"\nCRITICAL: Cannot open port {MAC_PORT}. Error: {e}")
        print("Ensure Arduino IDE Serial Monitor is closed.")
        os._exit(1)

    hw_status['serial_ok'] = True
    time.sleep(2)
    ser.write(b"k")  # Send knock

    # Handshake — wait for "System Ready"
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
                speak(filename=audio_map.get("System Ready"),
                      fallback_text=text_fallback["System Ready"], blocking=True)
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

        # Drain entire buffer before yielding (prevents audio lag)
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

                t = speak(filename=audio_map.get(message),
                          fallback_text=text_fallback.get(message, message), blocking=False)

                if "mission complete" in message.lower():
                    t.join()
                    speak(filename="outro.mp3",
                          fallback_text="Handover protocol concluded. Both systems returning to standby.",
                          blocking=True)
                    print("\n--- MISSION COMPLETE ---")
                    print(">> Type 'run' to restart, or 'exit' to quit.\n")

        time.sleep(0.005)

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    dash_url = f'http://{HOST}:{PORT}/'
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  J.A.R.V.I.S. — HANDOVER MODE")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Dashboard : {dash_url}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

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
                print("Shutting down J.A.R.V.I.S...")
                os._exit(0)
    except KeyboardInterrupt:
        os._exit(0)
