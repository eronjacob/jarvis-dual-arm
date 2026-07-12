# J.A.R.V.I.S. — Coordinated Dual-Arm Robotic System

> **EENG6010 Final Year Engineering Project**  
> University of Kent, School of Engineering  
> *Eron Jacob O. Buenaflor — eb546*  
> Supervised by Dr. Xinggang Yan

---

<div align="center">

![System Status](https://img.shields.io/badge/status-completed-brightgreen)
![Platform](https://img.shields.io/badge/platform-Arduino%20UNO%20R4%20WiFi-blue)
![Language](https://img.shields.io/badge/firmware-C%2B%2B-orange)
![Language](https://img.shields.io/badge/middleware-Python%203-yellow)
![Frontend](https://img.shields.io/badge/dashboard-Three.js%20%7C%20Chart.js-purple)
![Budget](https://img.shields.io/badge/total%20cost-£116.70-lightgrey)

</div>

---

## Overview

This project demonstrates that meaningful bimanual robotic coordination is achievable on a total component budget under **£120**. Two identical 6-DOF robotic arms — fabricated from 3D-printed PLA components and servo motors — are controlled by a single **Arduino UNO R4 WiFi** microcontroller via a **PCA9685 16-channel PWM servo driver**.

The system performs two distinct coordinated tasks:

| Task | Description |
|------|-------------|
| **Handover** | Left arm picks an object, rotates, and transfers it to the right arm at a shared handover point. The right arm carries it to a designated drop zone. |
| **Synchronised Pick-and-Place** | Both arms descend, grip, lift, hold, lower, and release a rigid payload simultaneously — demonstrating true bimanual coordination. |

A browser-based real-time monitoring dashboard (built with Three.js and Chart.js) displays live servo angles, 3D particle arm visualisation, and four live trajectory graphs throughout each task.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        HARDWARE LAYER                           │
│                                                                  │
│   Left Arm (6-DOF)          PCA9685           Arduino UNO R4   │
│   ├── Base (DM996)     ◄──  Ch 0–5   ◄── I2C ──  WiFi         │
│   ├── Shoulder (DM996) │                                         │
│   ├── Elbow (MG996R)   │                         │              │
│   ├── Wrist Roll (SG90)│    PCA9685              │ UART         │
│   ├── Wrist Pitch (SG90)    Ch 10–15  ◄──────────┘              │
│   └── Gripper (SG90)        │                                   │
│                             ▼                                    │
│   Right Arm (6-DOF) ◄── 6.7V / 3.1A DC Power Supply            │
└─────────────────────────────────────────────────────────────────┘
                              │ UART Serial (115200 baud)
┌─────────────────────────────▼───────────────────────────────────┐
│                        SOFTWARE LAYER (MacBook)                 │
│                                                                  │
│   robot_voice_5.py / robot_voice_6.py (Python Middleware)       │
│   ├── Serial handshake & telemetry parsing                       │
│   ├── Forward-kinematics computation                             │
│   ├── Audio engine (ElevenLabs MP3 / macOS TTS)                 │
│   └── Flask web server  ──► HTTP JSON endpoints                  │
│                                      │                           │
│                              ┌───────▼────────┐                  │
│                              │  Browser Dashboard               │
│                              │  dashboard_3/4.html              │
│                              │  ├── Three.js 3D visualisation   │
│                              │  ├── Chart.js trajectory graphs  │
│                              │  └── Live servo angle bars       │
│                              └────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
jarvis-dual-arm/
│
├── firmware/
│   ├── handover_task/
│   │   └── handover_task.ino          # Sequential handover firmware (smoothMove)
│   ├── coordinated_pickup/
│   │   └── coordinated_pickup.ino     # Synchronised LERP firmware (coordinatedMove)
│   └── prototype_test/
│       └── prototype_test.ino         # Early prototype / dev testing sketch
│
├── software/
│   ├── robot_voice_5_handover/
│   │   └── robot_voice_5.py           # Handover task middleware + Flask server
│   ├── robot_voice_6_coordinated/
│   │   └── robot_voice_6.py           # Coordinated pickup middleware + Flask server
│   └── templates/
│       ├── dashboard_3.html           # Handover task browser dashboard
│       └── dashboard_4.html           # Coordinated pickup browser dashboard
│
├── docs/
│   ├── HARDWARE.md                    # Wiring guide, servo allocation, BOM
│   ├── CALIBRATION.md                 # Joint characterisation & angle tables
│   └── KINEMATICS.md                  # FK equations and coordinate system
│
├── assets/
│   └── audio/                         # Pre-generated ElevenLabs MP3 files (not included)
│
├── .gitignore
├── LICENSE
└── README.md
```

---

## Hardware

### Components

| Component | Model | Qty | Supplier | Cost |
|-----------|-------|-----|----------|------|
| Microcontroller | Arduino UNO R4 WiFi | 1 | Pi Hut | £25.00 |
| Servo Driver | Dollatek PCA9685 16-ch | 1 | Amazon UK | £4.99 |
| Base/Shoulder Servos | Diymore DM996 (15 kg·cm) | 6-pack | Amazon UK | £27.98 |
| Elbow Servos | Yusvwkj MG996R (15 kg·cm) | 4-pack | Amazon UK | £21.99 |
| Wrist/Gripper Servos | SG90 Metal Gear (1.8 kg·cm) | 6-pack | Jennison Lab | £0.00 |
| Power Supply (primary) | GW Instek GPS-3303 (6.7V / 3.1A) | 1 | Lab | £0.00 |
| Power Supply (purchased) | COOLM 5V / 15A | 1 | Amazon UK | £17.99 |
| 3D Model STL Files | FABRI CREATOR 6-DOF | 1 | Cults3D | £6.09 |
| Jumper Wires | DuPont 40-pin × 2 | 2-pack | Bright Components UK | £4.67 |
| Power Cable | 14 AWG DC Female Pigtail | 1 | Amazon UK | £7.99 |
| **TOTAL** | | | | **£116.70** |

### Servo Allocation

| Joint | Servo Model | Left Arm Pin | Right Arm Pin |
|-------|-------------|-------------|--------------|
| Base | DM996 | 0 | 10 |
| Shoulder | DM996 | 1 | 11 |
| Elbow | MG996R | 2 | 12 |
| Wrist Roll | SG90 | 3 | 13 |
| Wrist Pitch | SG90 | 4 | 14 |
| Gripper | SG90 | 5 | 15 |

> Channels 6–9 are unused.

### Wiring

```
Arduino UNO R4 WiFi
├── A4 (SDA) ──────► PCA9685 SDA
├── A5 (SCL) ──────► PCA9685 SCL
└── 5V ────────────► PCA9685 VCC

GW Instek GPS-3303 (6.7V–6.8V)
└── V+ ────────────► PCA9685 V+ (servo power rail)

PCA9685 Channels 0–5  ──► Left Arm Servos
PCA9685 Channels 10–15 ─► Right Arm Servos
```

**⚠️ Important:** The PCA9685 logic supply (VCC) must be kept at 5V. Do not connect the servo power rail (V+) to the VCC pin. During the synchronised lift task, avoid sustained operation above 6.9V — the PCA9685 logic is rated to 6.0V max.

---

## Firmware

### Key Design Decisions

#### Dual PWM Range Mapping

The DM996/MG996R and SG90 servos share the same 50Hz frame but have different internal pulse thresholds. Two mapping ranges are defined:

```cpp
#define BIG_MIN   130   // DM996 / MG996R: Base, Shoulder, Elbow
#define BIG_MAX   600
#define SMALL_MIN 150   // SG90: Wrist Roll, Wrist Pitch, Gripper
#define SMALL_MAX 550
```

#### Knock-Knock Handshake

The Arduino UNO R4 WiFi resets when a serial connection is opened. Without a handshake, the Python host can begin transmitting before firmware initialisation is complete. The solution:

```cpp
// Arduino waits indefinitely for knock byte
while (Serial.available() <= 0) { delay(500); }
while (Serial.available() > 0)  { Serial.read(); }  // flush
broadcastAngles();
Serial.println("Action: System Ready");
```

```python
# Python sends knock, waits for "System Ready"
ser.write(b"k")
while not ready:
    line = ser.readline().decode().strip()
    if "System Ready" in line:
        ready = True
```

#### Motion Profiles

**Handover Task — `smoothMove()`**  
Sequential single-axis motion. Moves one joint at a time, one degree per step:

```cpp
void smoothMove(int pin, int targetAngle, int speedDelay) {
    // Increments ±1° per step with configurable delay
}
```

**Synchronised Task — `coordinatedMove()` (LERP Engine)**  
All active joints begin and finish at the exact same millisecond using floating-point linear interpolation:

```cpp
void coordinatedMove(int* pins, int* targets, int numServos, int durationMs) {
    // θᵢ(s) = θᵢ_start + (θᵢ_target − θᵢ_start) × (s / MOVE_STEPS)
    // Δt = durationMs / MOVE_STEPS
}
```

`MOVE_STEPS = 90` is defined globally. Using `float` rather than `int` for increments was critical — integer truncation caused joints with shorter travel distances to arrive early, creating mechanical shear on the payload.

---

## Software

### Python Middleware

Both `robot_voice_5.py` (handover) and `robot_voice_6.py` (coordinated) run three concurrent threads:

| Thread | Role |
|--------|------|
| **Serial Processing Thread** | Reads incoming `Servo:pin,angle` and `Action:label` lines; updates shared state |
| **Flask Web Server Thread** | Hosts `/data`, `/trajectory`, `/metrics` JSON endpoints at 127.0.0.1:5001 |
| **Main Execution Thread** | Handles terminal input (`run` / `exit`), triggers sequence, coordinates audio |

A `speak_lock` threading lock ensures only one audio announcement plays at a time, even if the Arduino sends two `Action:` events in rapid succession.

#### Serial Buffer Drain Fix

During the synchronised task, high-frequency telemetry caused audio to lag several seconds behind physical motion. Fix:

```python
# Read entire buffer before yielding, not line-by-line
while ser.in_waiting > 0:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    # process...
```

### Forward Kinematics

Gripper tip positions are computed from joint angles using vector-geometric forward kinematics. The Python middleware and browser dashboard run identical calculations so both always reflect the same arm configuration:

```
X = Σ Lᵢ · cos(Σ θⱼ)
Y = Σ Lᵢ · sin(Σ θⱼ)
```

Inter-gripper distance (synchronisation metric):

```
D_separation = √((xL−xR)² + (yL−yR)² + (zL−zR)²)
```

A flat, unchanging `D_separation` during the hold phase is the primary proof that both arms moved in perfect synchrony. The flat line confirms `dD/dt = 0` throughout the bilateral grip.

### Dashboard Features

| Feature | Handover (dashboard_3.html) | Coordinated Pick (dashboard_4.html) |
|---------|-----------------------------|--------------------------------------|
| 3D particle arm visualisation | ✅ | ✅ |
| Live servo angle bars (12 joints) | ✅ | ✅ |
| 4 real-time Chart.js trajectory graphs | ✅ | ✅ |
| Inter-gripper distance chart | ✅ | ✅ |
| Metrics strip (elapsed, samples, actions) | ✅ | ✅ |
| SYNCHRONISED PICK overlay badge | ❌ | ✅ |
| Amber gripper glow during bilateral hold | ❌ | ✅ |
| Auto-rotating 3D view (mouse-drag override) | ✅ | ✅ |
| LERP-smoothed 3D animation | ✅ | ✅ |

The dashboard polls `/data` every ~33ms and `/trajectory` every 250ms. Three.js renders at native frame rate with a separate LERP factor applied to display angles, preventing jitter from discrete servo step updates.

---

## Getting Started

### Prerequisites

```
Python 3.x
pip install pyserial flask
Arduino IDE 2.x
Adafruit PWM Servo Driver Library (via Arduino Library Manager)
```

### Running the Handover Task

1. Flash `firmware/handover_task/handover_task.ino` to the Arduino UNO R4 WiFi.
2. **Close** Arduino IDE Serial Monitor (it will block the Python serial connection).
3. Update `MAC_PORT` in `robot_voice_5.py` to match your Arduino's serial port:
   ```python
   MAC_PORT = '/dev/cu.usbmodem...'   # macOS
   # MAC_PORT = 'COM3'                # Windows
   ```
4. Place pre-generated ElevenLabs MP3 files in `~/Desktop/JARVIS_Audio/` (or update `AUDIO_DIR`). The system falls back to macOS `say` command if files are not found.
5. Run the middleware:
   ```bash
   python software/robot_voice_5_handover/robot_voice_5.py
   ```
6. Open `http://127.0.0.1:5001` in a browser.
7. Type `run` in the terminal to begin. Type `run` again to repeat. Type `exit` to quit.

### Running the Coordinated Pick-and-Place Task

1. Flash `firmware/coordinated_pickup/coordinated_pickup.ino`.
2. Run:
   ```bash
   python software/robot_voice_6_coordinated/robot_voice_6.py
   ```
3. Open `http://127.0.0.1:5001` and type `run`.

> **Power note:** The synchronised lift requires 6.8–7.0V to overcome stall conditions under dual-arm load. Keep runs short at 7.0V to protect the PCA9685 logic rail.

---

## Results

### Handover Task

- Successfully completed without mechanical collision in every supervised trial
- Inter-gripper separation closed from ~9–10 scene units (home) to ~1.5–2.0 at the handover point, confirming gripper alignment
- Step 3 (base rotation to 172°) was the most mechanically demanding moment; the DM996 delivered sufficient torque at 6.8V without stalling
- Repeatability affected by PWM jitter and thermal drift in plastic gear housings (~10–20mm variation between runs)

### Synchronised Pick-and-Place Task

- Payload remained visually level throughout the lift — confirming LERP synchronisation eliminated mechanical shear
- `D_separation` held constant (flat line) during the entire hold phase: `dD/dt = 0`
- Both left and right gripper distance-from-base charts showed identical linear slopes at each phase transition, confirming joint speed scaling was correct
- PSU temporarily increased to 7.0V for synchronised lift; restricted to short demonstrations due to PCA9685 voltage limit

---

## Safety

A DC bridge adapter borrowed from the Jennison laboratory emitted smoke during an early power-on test, caused by insufficient current rating for the connected load. The system was immediately powered down. The incident was reported to laboratory technicians and the Mechanical Engineering Officer in accordance with school safety procedures. No injury occurred.

**Lessons applied:**
- Verify component current and voltage ratings against datasheet specifications before connection
- Use only laboratory-grade power supplies with verified ratings
- Inspect all power connections before each session

---

## Future Work

| Area | Description |
|------|-------------|
| **Closed-loop control** | Magnetic absolute encoders at each joint for real-time backlash correction |
| **Isolated power topology** | Custom PCB separating 3.3V/5V I2C logic rails from 7.4V motor rail |
| **DH Parameter FK** | Replace vector-geometric FK with full Denavit-Hartenberg homogeneous transformation matrices, enabling inverse kinematics path planning |
| **WebSocket push** | Replace 100ms polling with WebSocket connection for lower dashboard latency |
| **Sensor integration** | Ultrasonic sensors and encoder feedback for dynamic pick-location detection |

---

## Acknowledgements

- **Dr. Xinggang Yan** — Project supervisor. His suggestion to incorporate real-time visualisation significantly elevated the technical depth of the final system.
- **Omar Dawaba & Mark Vogle** — Jennison Building mechanics, for fastener guidance and servo horn advice during mechanical assembly.
- **Ryan Morrow** — Mechanical Engineering Officer, for professional handling of the power supply safety incident.
- **Sam Hurford** — Peer who printed prototype components ahead of schedule on a personal Bambu Lab printer.
- **Jason Morris & Alp** — Electronic assistance including systems and power checks.
- **Nathan Brabon** — Component insight assistance.

---

## References

Key references from the project literature review:

1. Abbas, Narayan & Dwivedy (2023) — *A systematic review on cooperative dual-arm manipulators* — Int. J. Intell. Robot. Appl.
2. Nakano et al. (1974) — MELARM anthropomorphous dual-arm manipulator demonstration
3. Nakamura, Hanafusa & Yoshikawa (1987) — *Task-priority based redundancy control* — IJRR
4. Uchiyama & Dauchez (1993) — *Symmetric kinematic formulation for two-arm robots* — Advanced Robotics
5. Craig, J.J. (2005) — *Introduction to Robotics: Mechanics and Control*, 3rd ed. — Pearson

---

## Licence

This project is released for educational and research purposes.  
© 2026 Eron Jacob O. Buenaflor — University of Kent EENG6010

---

<div align="center">
<sub>J.A.R.V.I.S. PROTOCOL — UNIVERSITY OF KENT — SCHOOL OF ENGINEERING</sub>
</div>
