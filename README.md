<div align="center">

# J.A.R.V.I.S.
### Coordinated Dual-Arm Robotic System

**Final Year Engineering Dissertation Project**  

*Eron Jacob O. Buenaflor*

---

![Status](https://img.shields.io/badge/status-completed-brightgreen?style=flat-square)
![Platform](https://img.shields.io/badge/platform-Arduino%20UNO%20R4%20WiFi-00979D?style=flat-square&logo=arduino&logoColor=white)
![Firmware](https://img.shields.io/badge/firmware-C%2B%2B-orange?style=flat-square&logo=cplusplus&logoColor=white)
![Middleware](https://img.shields.io/badge/middleware-Python%203-3776AB?style=flat-square&logo=python&logoColor=white)
![Dashboard](https://img.shields.io/badge/dashboard-Three.js%20%7C%20Chart.js-purple?style=flat-square)
![Budget](https://img.shields.io/badge/total%20cost-£116.70%20%2F%20£120-lightgrey?style=flat-square)

</div>

---

## Overview

This project demonstrates that meaningful **bimanual robotic coordination** is achievable on a total component budget under **£120**. Two identical 6-DOF robotic arms — fabricated from 3D-printed PLA components and servo motors — are controlled by a single Arduino UNO R4 WiFi microcontroller via a PCA9685 16-channel PWM servo driver.

The system performs two distinct coordinated tasks and streams live telemetry to a browser-based monitoring dashboard built with Three.js and Chart.js.

| Task | Description |
|------|-------------|
| **Handover** | Left arm picks an object, rotates 172°, and transfers it to the right arm at a shared handover point. The right arm then carries it to a designated drop zone. |
| **Synchronised Pick-and-Place** | Both arms simultaneously descend, grip, lift, hold, lower, and release a rigid payload — demonstrating true bimanual coordination via a floating-point LERP engine. |

---

## Gallery

<div align="center">

### Physical System — Jennison Electronics Workshop, University of Kent

![Lab Setup](docs/images/lab_setup.jpg)

*Both 3D-printed 6-DOF arms mounted 570mm apart, connected to the GW Instek GPS-3303 laboratory power supply and MacBook running the Python middleware. The J.A.R.V.I.S. dashboard is visible on the laptop screen.*

---

### Real-Time Browser Dashboard

![Dashboard](docs/images/dashboard.png)

*Live monitoring dashboard showing both arms at home position after handshake. Left arm (blue) and right arm (orange) rendered as 130-particle 3D clouds via Three.js. Servo angle bars, metrics strip, and four Chart.js trajectory graphs all update in real time from Arduino telemetry.*

---

### CAD Model — FABRI CREATOR 6-DOF Arm (Cults3D)

| Home Position | Extended Position |
|:---:|:---:|
| ![CAD Home](docs/images/cad_home.png) | ![CAD Extended](docs/images/cad_extended.png) |

*The FABRI CREATOR design was converted from STEP to STL in Autodesk Fusion 360. Left and right arms were printed as mirror images. Key structural parts: 15% Gyroid infill at 0.2mm layer height. Precision gears: 40–45% infill at 0.15mm layer height.*

</div>

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         HARDWARE LAYER                           │
│                                                                  │
│  Left Arm (6-DOF)           PCA9685 (0x40)     Arduino UNO R4  │
│  ├── Base      DM996   ◄── Ch 0–5   ◄─── I2C ──── WiFi        │
│  ├── Shoulder  DM996   │   (400kHz)              │             │
│  ├── Elbow     MG996R  │                         │ UART        │
│  ├── Wrist Roll  SG90  │   PCA9685 (0x40)        │ 115200 baud │
│  ├── Wrist Pitch SG90  ◄── Ch 10–15 ◄────────────┘             │
│  └── Gripper   SG90        │                                    │
│                             ▼                                    │
│  Right Arm (6-DOF) ◄── GW Instek GPS-3303  (6.7V / 3.1A)      │
└─────────────────────────────┬────────────────────────────────────┘
                              │ UART Serial
┌─────────────────────────────▼────────────────────────────────────┐
│                      SOFTWARE LAYER (MacBook)                    │
│                                                                  │
│  robot_voice_5.py / robot_voice_6.py                            │
│  ├── Thread 1: Serial — handshake, telemetry parsing, FK        │
│  ├── Thread 2: Flask  — /data  /trajectory  /metrics            │
│  └── Thread 3: Main   — terminal input, audio (speak_lock)      │
│                                    │ HTTP JSON (localhost:5001)  │
│                            ┌───────▼──────────┐                 │
│                            │  Browser Dashboard                 │
│                            │  dashboard_3/4.html                │
│                            │  · Three.js 3D particle arms       │
│                            │  · Chart.js trajectory graphs      │
│                            │  · Live servo angle bars           │
│                            └──────────────────┘                 │
└──────────────────────────────────────────────────────────────────┘
```

---

## Repository Structure

```
jarvis-dual-arm/
│
├── firmware/
│   ├── handover_task/
│   │   └── handover_task.ino          ← Sequential handover (smoothMove engine)
│   ├── coordinated_pickup/
│   │   └── coordinated_pickup.ino     ← Synchronised LERP (coordinatedMove engine)
│   └── prototype_test/
│       └── prototype_test.ino         ← Early development / calibration sketch
│
├── software/
│   ├── robot_voice_5_handover/
│   │   └── robot_voice_5.py           ← Handover middleware + Flask + ElevenLabs audio
│   ├── robot_voice_6_coordinated/
│   │   └── robot_voice_6.py           ← Coordinated middleware + Flask + Samantha TTS
│   └── templates/
│       ├── dashboard_3.html           ← Handover dashboard (Three.js + Chart.js)
│       └── dashboard_4.html           ← Coordinated dashboard (+ amber glow, sync badge)
│
├── docs/
│   ├── PROJECT_EXPLAINED.md           ← Deep-dive: all algorithms, maths, design decisions
│   ├── HARDWARE.md                    ← Wiring guide, servo allocation, power findings
│   ├── CALIBRATION.md                 ← Joint characterisation tables, PWM mapping
│   ├── KINEMATICS.md                  ← FK equations, LERP derivation, coordinate system
│   └── images/                        ← Project photos and CAD screenshots
│
├── assets/
│   └── audio/README.md                ← ElevenLabs MP3 file list and narration text
│
├── .gitignore
├── LICENSE
└── README.md
```

---

## Hardware

### Bill of Materials

| Component | Model | Role | Qty | Supplier | Cost |
|-----------|-------|------|-----|----------|------|
| Microcontroller | [Arduino UNO R4 WiFi](https://thepihut.com/products/arduino-uno-r4-wifi?variant=42470106235075) | Main controller | 1 | The Pi Hut | £25.00 |
| Servo Driver | [DollaTek PCA9685 16-ch](https://www.amazon.co.uk/DollaTek-PCA9685-Channel-12-bit-Driver/dp/B0BKZC1XWR/) | 12-bit PWM over I2C | 1 | Amazon UK | £4.99 |
| Base/Shoulder Servos | [Alinan MG996R 6-pack](https://www.amazon.co.uk/Alinan-MG996R-Neutral-Digital-Helicopter/dp/B09V52BD8Q/) | 15 kg·cm, base & shoulder | 6 | Amazon UK | £23.99 |
| Elbow Servos | [Yusvwkj MG996R 4-pack](https://www.amazon.co.uk/yusvwkj-Helicopter-Airplane-Mechanical-Waterproof/dp/B09GDXLZ28/) | 15 kg·cm, elbow joints | 4 | Amazon UK | £13.99 |
| Wrist/Gripper Servos | SG90 Metal Gear 6-pack | 1.8 kg·cm, distal joints | 6 | Jennison Lab | £0.00 |
| Power Supply (lab) | GW Instek GPS-3303 | 6.7V / 3.1A (primary) | 1 | Lab | £0.00 |
| Power Supply (purchased) | [COOLM 5V / 15A](https://www.amazon.co.uk/5V-15A-Power-Supply-Adapter/dp/B0G7SRP2V5/) | Backup / initial testing | 1 | Amazon UK | £17.99 |
| 3D Model Files | [FABRI CREATOR 6-DOF (Cults3D)](https://cults3d.com/en/3d-model/gadget/brazo-robotico-con-arduino-step-files-robotic-arm-guardar-reproducir-export) | Arm STL/STEP files | 1 set | Cults3D | £6.09 |
| Jumper Wires | [DuPont 40-pin × 2 packs](https://store.brightcomponents.co.uk/basket/) | Signal wiring | 80 | Bright Components UK | £4.57 |
| Power Cable | [14 AWG DC Female Pigtail](https://www.amazon.co.uk/CERRXIAN-DC5525-Pigtails-Female-Security/dp/B0BK9Q748H/) | PSU to PCA9685 V+ | 1 | Amazon UK | £7.99 |
| Fasteners | M3 screws, nuts, washers | Assembly hardware | — | Jennison Lab | £0.00 |
| **TOTAL** | | | | | **£116.70** |

> 💡 The 5V/15A COOLM supply was found to be insufficient during testing — servo motors require 6.0–7.4V for reliable torque. The GW Instek lab supply at 6.7V was used for all final testing. See [HARDWARE.md](docs/HARDWARE.md) for the full power findings.

### Servo Allocation

| Joint | Role | Servo Model | Stall Torque | Left Arm (Pin) | Right Arm (Pin) |
|-------|------|-------------|-------------|----------------|-----------------|
| Base | Full arm rotation | DM996 | 15 kg·cm | 0 | 10 |
| Shoulder | Primary load-bearing | DM996 | 15 kg·cm | 1 | 11 |
| Elbow | Secondary structural | MG996R | 15 kg·cm | 2 | 12 |
| Wrist Roll | Light distal | SG90 | 1.8 kg·cm | 3 | 13 |
| Wrist Pitch | Light distal | SG90 | 1.8 kg·cm | 4 | 14 |
| Gripper | Object grasping | SG90 | 1.8 kg·cm | 5 | 15 |

> PCA9685 channels 6–9 are unused.

### Wiring Diagram

```
Arduino UNO R4 WiFi          PCA9685 (I2C Address: 0x40)
─────────────────────────────────────────────────────────
A4  (SDA)       ──────────►  SDA
A5  (SCL)       ──────────►  SCL
5V              ──────────►  VCC  (logic supply only — max 6V)
GND             ──────────►  GND

GW Instek GPS-3303
─────────────────────────────────────────────────────────
6.7V output     ──────────►  PCA9685 V+  (servo power rail)
GND             ──────────►  PCA9685 GND

PCA9685 Channels 0–5   ──►  Left Arm  (Base → Gripper)
PCA9685 Channels 10–15 ──►  Right Arm (Base → Gripper)
```

> ⚠️ **Critical:** Keep PCA9685 VCC at 5V (logic only). The servo V+ rail can run at 6.7V–7.0V. Do **not** share these rails — doing so risks damaging the PCA9685 logic circuitry.

---

## Firmware

### Motion Engines

Two distinct motion profiles are used across the two tasks:

#### `smoothMove()` — Sequential Single-Axis (Handover Task)

Moves one joint at a time, one degree per step. Simple and reliable for sequential arm movements:

```cpp
void smoothMove(int pin, int targetAngle, int speedDelay) {
    for (int i = startAngle; i <= targetAngle; i++) {
        setAngle(pin, i);
        delay(speedDelay);  // e.g. 13ms per degree
    }
    broadcastAngles();  // Tell Python the updated state
}
```

#### `coordinatedMove()` — Floating-Point LERP Engine (Synchronised Task)

All joints begin and finish at the **exact same millisecond**, regardless of individual travel distance. This was the critical firmware development that enabled true bimanual coordination:

```cpp
// θᵢ(s) = θᵢ_start + (θᵢ_target − θᵢ_start) × (s / MOVE_STEPS)
// Δt    = durationMs / MOVE_STEPS    (MOVE_STEPS = 90)

void coordinatedMove(int* pins, int* targets, int numServos, int durationMs) {
    float startAngles[MAX_SERVOS];
    float increments[MAX_SERVOS];  // ← Must be float, NOT int

    for (int i = 0; i < numServos; i++) {
        startAngles[i] = currentAngles[pins[i]];
        increments[i]  = (float)(targets[i] - startAngles[i]) / MOVE_STEPS;
    }
    for (int s = 1; s <= MOVE_STEPS; s++) {
        for (int i = 0; i < numServos; i++) {
            setAngle(pins[i], startAngles[i] + (increments[i] * s));
        }
        delay(durationMs / MOVE_STEPS);
    }
}
```

> **Why float?** Integer truncation of small increments (e.g. 9° ÷ 90 steps = 0.1° per step → truncated to 0) causes joints to arrive at different times, creating mechanical shear on the payload. `float` eliminates this entirely.

### Knock-Knock Handshake

The Arduino UNO R4 WiFi resets on serial connection open. Without a handshake, commands arrive before firmware initialisation completes:

```cpp
// Arduino side — holds all execution until Python is ready
while (Serial.available() <= 0) { delay(500); }
while (Serial.available() > 0)  { Serial.read(); }  // flush knock byte
broadcastAngles();
Serial.println("Action: System Ready");
```

```python
# Python side — sends knock, waits for confirmation
ser.write(b"k")
while not ready:
    if "System Ready" in ser.readline().decode():
        ready = True
```

### Dual PWM Mapping

DM996/MG996R and SG90 servos use different pulse width ranges despite sharing the same 50Hz frame:

```cpp
#define BIG_MIN   130   // DM996 / MG996R  (Base, Shoulder, Elbow)
#define BIG_MAX   600
#define SMALL_MIN 150   // SG90  (Wrist Roll, Wrist Pitch, Gripper)
#define SMALL_MAX 550
```

---

## Software

### Python Middleware — Three-Thread Architecture

```
┌─────────────────┐    cmd_queue     ┌──────────────────────────────┐
│   MAIN THREAD   │ ──────────────► │      SERIAL THREAD           │
│                 │                  │  · Opens serial port         │
│  Terminal input │                  │  · Sends knock byte          │
│  run / exit     │                  │  · Drains buffer each loop   │
│  Audio at end   │                  │  · Parses Servo:pin,angle    │
└─────────────────┘                  │  · Parses Action:label       │
                                     │  · Calls update_trajectory() │
                    servo_angles{}   └──────────────────────────────┘
                    trajectory{}              │
                    (trajectory_lock)         │ shared state
                                     ┌────────▼─────────────────────┐
                                     │      FLASK THREAD            │
                                     │  GET /data       → angles    │
                                     │  GET /trajectory → FK data   │
                                     │  GET /metrics    → distances │
                                     └──────────────────────────────┘
```

### Forward Kinematics

Gripper tip position (X, Y, Z) is computed from joint angles using vector-geometric FK. Both Python and the browser dashboard run identical calculations to stay in sync:

$$X = \sum_{i=1}^{n} L_i \cdot \cos\left(\sum_{j=1}^{i} \theta_j\right)$$

$$Y = \sum_{i=1}^{n} L_i \cdot \sin\left(\sum_{j=1}^{i} \theta_j\right)$$

### Inter-Gripper Distance — Synchronisation Metric

The primary proof of bilateral synchronisation. A perfectly flat line during the hold phase (`dD/dt = 0`) confirms no timing lag between the two arms:

$$D_{separation} = \sqrt{(x_L - x_R)^2 + (y_L - y_R)^2 + (z_L - z_R)^2}$$

### Dashboard Feature Comparison

| Feature | Handover `dashboard_3.html` | Coordinated `dashboard_4.html` |
|---------|:---:|:---:|
| 3D particle arm visualisation (130 particles/arm) | ✅ | ✅ |
| 12 live servo angle bars | ✅ | ✅ |
| 4 real-time Chart.js trajectory graphs | ✅ | ✅ |
| Inter-gripper separation chart | ✅ | ✅ |
| Metrics strip (elapsed / samples / actions) | ✅ | ✅ |
| Auto-rotating 3D view (mouse-drag override) | ✅ | ✅ |
| LERP-smoothed 3D animation | ✅ | ✅ |
| **SYNCHRONISED PICK** overlay badge | ❌ | ✅ |
| Amber gripper glow during bilateral hold | ❌ | ✅ |
| Amber inter-gripper bar pulse during grip | ❌ | ✅ |
| Recursive `setTimeout` polling (anti-lag) | ❌ | ✅ |

---

## Getting Started

### Prerequisites

```bash
# Python dependencies
pip install pyserial flask

# Arduino IDE 2.x — install via Library Manager:
#   Adafruit PWM Servo Driver Library
```

### Running the Handover Task

```bash
# 1. Flash firmware
#    Open firmware/handover_task/handover_task.ino in Arduino IDE
#    Upload to Arduino UNO R4 WiFi
#    Close Serial Monitor before running Python

# 2. Update your serial port in robot_voice_5.py:
#    MAC_PORT = '/dev/cu.usbmodem...'   (find yours in Arduino IDE → Tools → Port)

# 3. Place ElevenLabs MP3 files in ~/Desktop/JARVIS_Audio/
#    (falls back to macOS 'say' command automatically if not found)

# 4. Run the middleware
python software/robot_voice_5_handover/robot_voice_5.py

# 5. Open the dashboard
#    → http://127.0.0.1:5001

# 6. In the terminal, type:
#    run    ← starts the sequence
#    run    ← repeats it
#    exit   ← shuts down
```

### Running the Coordinated Pick-and-Place Task

```bash
# 1. Flash firmware/coordinated_pickup/coordinated_pickup.ino

# 2. Run the middleware (uses macOS Samantha TTS — no MP3 files needed)
python software/robot_voice_6_coordinated/robot_voice_6.py

# 3. Open http://127.0.0.1:5001
# 4. Type: run
```

> ⚠️ **Power note:** The synchronised bilateral lift requires 6.8–7.0V. Keep runs short at 7.0V — the PCA9685 logic VCC is rated to 6.0V max. See [HARDWARE.md](docs/HARDWARE.md#power-supply-findings) for full details.

---

## Results

### Handover Task

- Completed without mechanical collision in every supervised trial
- Inter-gripper separation closed from ~9–10 scene units (home) to ~1.5–2.0 units at the handover exchange point
- Step 3 (base rotation to 172°) was the most mechanically demanding — DM996 delivered sufficient torque at 6.8V without stalling
- Repeatability: ~10–20mm variation between runs, attributable to PWM jitter and thermal drift in plastic gear housings

### Synchronised Pick-and-Place Task

- Payload remained visually level throughout the lift — LERP synchronisation eliminated mechanical shear
- `D_separation` held constant during the entire hold phase, confirming `dD/dt = 0`
- Charts 1 & 2 showed identical linear slopes at every phase transition — joint speed scaling was correct
- Both arms required PSU voltage temporarily raised to 7.0V for the bilateral lift; demonstrations kept short to protect the PCA9685

---

## Key Engineering Findings

| Finding | Detail |
|---------|--------|
| **Voltage, not current, is the limiting factor** | DM996 servos need 6.0–7.4V. A 5V/15A supply fails not from insufficient current, but from insufficient voltage — the motor cannot generate enough magnetic torque at 5V |
| **Float vs Integer in LERP** | Integer truncation of small increments (e.g. 0.1° → 0) causes joint-arrival ordering errors and mechanical shear. Float arithmetic eliminates this |
| **Infill density vs servo load** | 15% Gyroid infill kept arm mass low enough for the shoulder servo to complete full range of motion. Higher infill increased servo loading toward stall |
| **Serial buffer drain** | Reading `ser.in_waiting` completely each loop (vs one line per cycle) reduced audio-to-motion lag from ~4 seconds to milliseconds |
| **Wire management in rotating joints** | Unsecured jumper wires inside the base joint resisted rotation at 172°, creating variable mechanical load that software could not compensate for |

---

## Future Work

| Area | Description |
|------|-------------|
| **Closed-loop control** | Magnetic absolute encoders at each joint for real-time backlash correction, targeting sub-5mm repeatability |
| **Isolated power topology** | Custom PCB separating 3.3V/5V I2C logic rails from 7.4V motor rail — eliminates overvoltage risk to PCA9685 |
| **DH Parameter FK + IK** | Full Denavit-Hartenberg homogeneous transformation matrices to enable true inverse kinematics path planning |
| **WebSocket streaming** | Replace 100ms HTTP polling with WebSocket push for lower dashboard latency and higher trajectory resolution |
| **Sensor integration** | Ultrasonic distance sensors and encoder feedback for dynamic pick-location detection without pre-programmed coordinates |

---

## Documentation

| Document | Contents |
|----------|----------|
| [PROJECT_EXPLAINED.md](docs/PROJECT_EXPLAINED.md) | Full deep-dive: all algorithms, mathematics, design decisions, and engineering findings |
| [HARDWARE.md](docs/HARDWARE.md) | Wiring guide, component ratings, power findings, safety incident record |
| [CALIBRATION.md](docs/CALIBRATION.md) | Joint characterisation tables, PWM mapping, pre-assembly procedure |
| [KINEMATICS.md](docs/KINEMATICS.md) | FK derivation, LERP mathematics, coordinate system, model limitations |

---

## Safety

During an early power-on test, a DC bridge adapter borrowed from the Jennison laboratory emitted smoke when connected to the COOLM supply — attributable to insufficient current rating for the connected load. The system was immediately powered down and reported to the laboratory technicians and Ryan Morrow (Mechanical Engineering Officer) in accordance with school safety procedures. No injury occurred.

**Lessons applied:**
- Verify voltage **and** current ratings against datasheet specifications before connecting any component to a power supply
- Use laboratory-grade supplies with verified ratings for all servo work
- Inspect all power connections before each session

---

## Acknowledgements

| Person | Contribution |
|--------|-------------|
| **Dr. Xinggang Yan** | Project supervisor. Suggested real-time visualisation and coordinated pick-and-place task extension, which significantly elevated the system's technical scope |
| **Omar Dawaba** | Jennison makerspace mechanic — fastener specification and drilling guidance during prototype assembly |
| **Mark Vogle** | Jennison makerspace mechanic — servo horn advice; recommended metal horns to prevent cyclic wear |
| **Ryan Morrow** | Mechanical Engineering Officer — handled the power supply safety incident professionally and constructively |
| **Sam Hurford** | Printed prototype components on a personal Bambu Lab printer ahead of schedule, enabling development during the Makerspace closure |
| **Jason Morris & Alp** | Electronic assistance including systems and power checks |
| **Nathan Brabon** | Component selection insight |

---

## References

1. Abbas, Narayan & Dwivedy (2023) — *A systematic review on cooperative dual-arm manipulators* — Int. J. Intell. Robot. Appl. 7, 683–707
2. Nakano et al. (1974) — MELARM anthropomorphous dual-arm manipulator
3. Nakamura, Hanafusa & Yoshikawa (1987) — *Task-priority based redundancy control of robot manipulators* — IJRR
4. Uchiyama & Dauchez (1993) — *Symmetric kinematic formulation for two-arm robots* — Advanced Robotics
5. Craig, J.J. (2005) — *Introduction to Robotics: Mechanics and Control*, 3rd ed. — Pearson Education

---

## Licence

Released for educational and research purposes.  
© 2026 Eron Jacob O. Buenaflor — University of Kent

---

<div align="center">
<sub>⚙ &nbsp; J.A.R.V.I.S. PROTOCOL &nbsp; ⚙</sub>
</div>
