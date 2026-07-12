# Project Deep-Dive: How J.A.R.V.I.S. Works

> A complete explanation of the design, algorithms, mathematics, and engineering decisions behind the dual 6-DOF robotic arm coordination system.

---

## Table of Contents

1. [What the Project Is and Why It Exists](#1-what-the-project-is-and-why-it-exists)
2. [System Overview — The Four Layers](#2-system-overview--the-four-layers)
3. [Mechanical Design](#3-mechanical-design)
4. [Electronics Architecture](#4-electronics-architecture)
5. [Servo Motor Control — PWM Fundamentals](#5-servo-motor-control--pwm-fundamentals)
6. [The Two Tasks Explained](#6-the-two-tasks-explained)
7. [Firmware Algorithms](#7-firmware-algorithms)
8. [Python Middleware — How the Three Threads Work](#8-python-middleware--how-the-three-threads-work)
9. [Forward Kinematics — The Mathematics](#9-forward-kinematics--the-mathematics)
10. [Inter-Gripper Distance — The Synchronisation Proof](#10-inter-gripper-distance--the-synchronisation-proof)
11. [The Browser Dashboard — 3D Visualisation and Charts](#11-the-browser-dashboard--3d-visualisation-and-charts)
12. [Audio System Design](#12-audio-system-design)
13. [Key Engineering Findings](#13-key-engineering-findings)
14. [What Could Be Improved](#14-what-could-be-improved)

---

## 1. What the Project Is and Why It Exists

### The Problem

Most undergraduate robotics courses use either expensive commercial platforms (well beyond typical teaching budgets) or very simple single-joint systems that cannot demonstrate meaningful coordination. There is a gap: platforms that are cheap enough for student labs but capable enough to demonstrate real bimanual manipulation.

### The Solution

This project built a **dual 6-DOF robotic arm system** from scratch for under £120, capable of performing two genuinely coordinated tasks:

- A **handover** — left arm picks an object, transfers it to the right arm
- A **synchronised pick-and-place** — both arms grip, lift, hold, and lower a rigid payload together

The system is not just a physical robot. It includes a complete software stack: embedded firmware on a microcontroller, a Python middleware layer that runs on a laptop, and a browser-based real-time monitoring dashboard that visualises both arms in 3D and plots trajectory data live.

### Why "J.A.R.V.I.S."?

The project adopts the aesthetic of the AI assistant from the Iron Man films — a deliberate design choice to make the demonstration engaging and to justify the use of an AI voice narration system. The handover task uses ElevenLabs-generated British-accent audio (George voice, matching the J.A.R.V.I.S. character) while the coordinated task uses the macOS Samantha TTS voice styled after F.R.I.D.A.Y.

---

## 2. System Overview — The Four Layers

The system has four distinct subsystems that communicate in a strict hierarchy:

```
Layer 1 — PHYSICAL HARDWARE
    Two 6-DOF 3D-printed PLA arms
    12 servo motors total (6 per arm)
    GW Instek GPS-3303 DC power supply (6.7V / 3.1A)
         |
         | PWM signals (50Hz)
         ↓
Layer 2 — EMBEDDED CONTROL (Arduino UNO R4 WiFi)
    PCA9685 16-channel PWM servo driver (I2C)
    Translates angle commands into servo pulses
    Runs motion sequences (smoothMove / coordinatedMove)
    Broadcasts servo angles over serial after each step
         |
         | UART serial 115200 baud
         ↓
Layer 3 — PYTHON MIDDLEWARE (MacBook)
    robot_voice_5.py / robot_voice_6.py
    Handles serial handshake and telemetry parsing
    Computes forward kinematics from joint angles
    Plays audio announcements (ElevenLabs MP3 / macOS TTS)
    Hosts Flask web server for dashboard data
         |
         | HTTP JSON (localhost:5001)
         ↓
Layer 4 — BROWSER DASHBOARD (HTML/JS)
    dashboard_3.html / dashboard_4.html
    Three.js 3D particle visualisation
    Chart.js real-time trajectory graphs
    Servo angle bars (12 joints live)
```

Each layer has exactly one job. The Arduino moves the arms. Python orchestrates and measures. The browser displays. This separation is a deliberate software architecture choice — it keeps each component independently testable and replaceable.

---

## 3. Mechanical Design

### The 6-DOF Arm

Each arm has six degrees of freedom, meaning six independently controllable joints. This is the minimum needed to both **position** (x, y, z) and **orient** (pitch, roll, yaw) the gripper tip freely in 3D space. Fewer DOF arms lack the freedom to perform the handover task, which requires simultaneous positioning and orientation control.

The six joints from base to tip:

```
Joint 1: Base Rotation    — rotates the entire arm around its vertical axis
Joint 2: Shoulder         — tilts the upper arm forward/backward
Joint 3: Elbow            — bends the forearm relative to the upper arm
Joint 4: Wrist Roll       — rotates the wrist assembly
Joint 5: Wrist Pitch      — tilts the wrist up/down
Joint 6: Gripper          — opens and closes the two-finger end-effector
```

This structure mirrors the standard 6-DOF industrial robot (PUMA 560 architecture), which became the norm in 1978 because it provides independent control of all six spatial variables.

### 3D Printing Decisions

Two different infill strategies were used:

| Part Type | Infill | Why |
|-----------|--------|-----|
| Structural arms, base | 15% Gyroid | Low weight reduces servo torque demand on upstream joints |
| Gears, central shaft | 40–45% | Gear tooth deformation under load required higher density |

This mattered significantly in practice. Higher infill increases rigidity but also increases mass, which increases the torque demand on every joint that must support that mass. The shoulder servo at 15% infill could complete its full range of motion reliably; with the same arm printed at higher infill, the shoulder would stall under load.

The two arms are mirror images of each other, mounted **570mm apart** on a shared workbench. This distance was not arbitrary — it was determined empirically by positioning both arms at their handover extension angles and confirming the grippers had clearance at the intended transfer point.

---

## 4. Electronics Architecture

### Why a PCA9685?

The Arduino UNO R4 WiFi has a limited number of hardware PWM output pins. Twelve servo motors each requiring an independent 50Hz PWM signal exceeds what the microcontroller can generate natively. The **PCA9685** is a dedicated 16-channel 12-bit PWM driver that connects to the Arduino via I2C, offloading all PWM generation to dedicated hardware.

I2C (Inter-Integrated Circuit) uses just two wires:
- **SDA** (Serial Data Line) — carries data, connected to Arduino A4
- **SCL** (Serial Clock Line) — provides synchronisation clock, connected to Arduino A5

The PCA9685 address is set to 0x40 via its hardware address pins.

### Power Rail Separation

This is critical and was one of the most important lessons of the project. Two separate power rails exist:

```
Arduino 5V rail → PCA9685 VCC (logic supply only)
GW Instek GPS-3303 → PCA9685 V+ (servo motor supply: 6.7V / 3.1A)
```

The servo motors must **not** be powered from the Arduino 5V rail. The Arduino cannot supply the current the motors require. Powering servos from the Arduino would destroy it. The V+ terminal on the PCA9685 is electrically isolated from VCC precisely to allow this separation.

### Why 6.7–6.8V, Not 5V?

The DM996 servos are specified for operation between 6V and 7.4V. At 5V:
- The shoulder servo stalls when the arm is at full extension
- The base rotation servo cannot overcome the gravitational load of the extended arm

At 6.8V all movements complete reliably. This finding contradicted the initial assumption that a 5V/15A supply would be sufficient. It was voltage, not current, that was the limiting factor.

---

## 5. Servo Motor Control — PWM Fundamentals

### How a Servo Motor Works

A standard RC servo receives a 50Hz PWM (Pulse-Width Modulation) signal. The width of the high pulse in each 20ms frame determines the servo's target angle:

```
Pulse width ~500µs  →  0°
Pulse width ~1500µs →  90°  (mid-point / neutral)
Pulse width ~2500µs →  180°
```

The servo motor has an internal potentiometer on its output shaft and a control circuit that continuously compares its actual position to the commanded position. If they differ, the motor drives until they match.

### The PCA9685 Pulse Count System

The PCA9685 generates 12-bit PWM values (0–4095 counts per 20ms frame). To drive a servo to a specific angle, the angle is first converted to a pulse count:

```cpp
// For large servos (DM996 / MG996R):
int pulse = map(angle, 0, 180, 130, 600);

// For small servos (SG90):
int pulse = map(angle, 0, 180, 150, 550);
```

The values 130, 600, 150, 550 are not from a datasheet — they were **calibrated empirically**. Every servo model has slightly different internal timing characteristics. The calibration process involved:
1. Commanding 0°, 90°, and 180°
2. Observing the physical arm position
3. Adjusting SERVOMIN and SERVOMAX until the commanded and actual angles matched

Two different ranges are needed because DM996/MG996R and SG90 servos have different internal pulse thresholds despite both using 50Hz frames.

---

## 6. The Two Tasks Explained

### Task 1: Object Handover

The handover is a **master-slave** coordination pattern. The left arm acts as master (initiates and controls the sequence) while the right arm acts as slave (responds to a predetermined cue).

The nine-step sequence:

```
Step 1: LEFT ARM PICK
  → Shoulder, elbow, wrist descend to pick position
  → Gripper closes on the cube

Step 2: CENTERING
  → Wrist pitch, elbow, shoulder return partway to distribute
    the payload mass more evenly before rotation

Step 3: ROTATE TO HANDOVER
  → Base servo drives to 172° — the most mechanically demanding
    movement, placing the full arm weight at maximum extension

Step 4: EXTEND LEFT ARM
  → Shoulder and elbow extend toward the right arm's intercept zone

Step 5: RIGHT ARM RECEIVE
  → Right arm base, shoulder, elbow move to intercept coordinates
  → Right gripper closes on the object

Step 6: LEFT ARM RELEASE
  → Left gripper opens — object transfers between grippers

Step 7: RIGHT ARM MOVES TO DROP ZONE
  → Right arm carries the object to a designated location

Step 8: FINAL DROP
  → Right gripper opens — object released

Step 9: RETURN HOME
  → Both arms return to their neutral positions sequentially
```

### Task 2: Synchronised Pick-and-Place

The coordinated pick is a **symmetric** coordination pattern. Both arms must execute the same motion profile simultaneously, because they are jointly holding a single rigid object. Any timing difference creates mechanical forces that would rotate or eject the payload.

The seven phases:

```
Phase 1 APPROACH:  Both arms descend together (Shoulder 130°, Elbow 22°)
Phase 2 GRAB:      Both grippers close simultaneously
Phase 3 LIFT:      Both arms rise together (Shoulder 90°, Elbow 91°)
Phase 4 HOLD:      All joints stationary for 2500ms
Phase 5 LOWER:     Both arms descend back to pick position
Phase 6 RELEASE:   Both grippers open simultaneously
Phase 7 HOME:      Two-step return (arms up first, then wrists restore)
```

The key difference from the handover task: in the coordinated task, **any motion must be performed by both arms at identical velocity**. This is why the motion engine had to be completely redesigned.

---

## 7. Firmware Algorithms

### Algorithm 1: smoothMove() — Sequential Single-Axis Motion

Used in the handover task. Moves one joint at a time, one degree per step:

```cpp
void smoothMove(int pin, int targetAngle, int speedDelay) {
    int startAngle = currentAngles[pin];
    if (startAngle < targetAngle) {
        for (int i = startAngle; i <= targetAngle; i++) {
            setAngle(pin, i);
            delay(speedDelay);  // e.g., 13ms per degree = ~130ms for 10°
        }
    } else {
        for (int i = startAngle; i >= targetAngle; i--) {
            setAngle(pin, i);
            delay(speedDelay);
        }
    }
    currentAngles[pin] = targetAngle;
    broadcastAngles();  // Tell Python the new state
}
```

This works well for single-arm motions but produces a sequential, staircase motion when multiple joints need to move together. It is fundamentally incompatible with the synchronised task.

### Algorithm 2: coordinatedMove() — LERP Multi-Joint Engine

This is the core innovation of the project. All joints begin and complete their travel at the exact same millisecond, regardless of how far each individual joint needs to move.

**The mathematics:** Linear Interpolation (LERP)

For each servo i, at step s out of MOVE_STEPS total steps:

```
θᵢ(s) = θᵢ_start + (θᵢ_target − θᵢ_start) × (s / MOVE_STEPS)
```

The time interval between steps:
```
Δt = durationMs / MOVE_STEPS
```

**In code:**

```cpp
#define MOVE_STEPS 90  // 90 steps per move

void coordinatedMove(int* pins, int* targets, int numServos, int durationMs) {
    int stepDelay = max(1, durationMs / MOVE_STEPS);

    float startAngles[MAX_SERVOS];
    float increments[MAX_SERVOS];

    // Pre-calculate the per-step increment for every joint
    for (int i = 0; i < numServos; i++) {
        startAngles[i] = currentAngles[pins[i]];
        increments[i]  = (float)(targets[i] - startAngles[i]) / MOVE_STEPS;
    }

    // Execute all 90 steps
    for (int s = 1; s <= MOVE_STEPS; s++) {
        for (int i = 0; i < numServos; i++) {
            float angle = startAngles[i] + (increments[i] * s);
            setAngle(pins[i], angle);
        }
        delay(stepDelay);
    }
}
```

**Why float, not int?**

This is the critical insight. Suppose a joint needs to move only 9 degrees over 90 steps. The increment is 9/90 = 0.1° per step. With integer arithmetic:

```
int increment = (int)(9 / 90) = (int)(0.1) = 0  // truncated to zero!
```

The joint would never move. Or more precisely, different joints would arrive at different times depending on how rounding happened to work out. In the physical system, this means one gripper reaches the object before the other — creating a torque on the payload that either ejects it or damages the arm.

With `float` arithmetic, each joint tracks its exact decimal position every step, and all joints finish simultaneously.

### Algorithm 3: The Knock-Knock Handshake

The Arduino UNO R4 WiFi automatically resets whenever a serial connection is opened. Without a handshake, the Python middleware might start sending commands before the firmware has finished initialising — the servos would receive garbage commands and snap to random positions.

**Solution:**

```
ARDUINO SIDE:
  while (Serial.available() <= 0) { delay(500); }  // Wait indefinitely
  while (Serial.available() > 0)  { Serial.read(); }  // Flush the knock byte
  broadcastAngles();
  Serial.println("Action: System Ready");

PYTHON SIDE:
  time.sleep(2)      # Wait for Arduino boot
  ser.write(b"k")    # Send the knock
  while not ready:
    line = ser.readline()
    if "System Ready" in line:
        ready = True
        # Now safe to begin
```

This ensures the physical arms only move after Python has confirmed it is listening and ready. It also prevents any commands from being lost in the buffer during startup.

### Algorithm 4: broadcastAngles() — Serial Telemetry Protocol

After every move, the Arduino broadcasts the current angle of all 16 channels:

```cpp
void broadcastAngles() {
    for (int i = 0; i < 16; i++) {
        Serial.print("Servo:");
        Serial.print(i);
        Serial.print(",");
        Serial.println((int)round(currentAngles[i]));
    }
}
```

This produces lines like:
```
Servo:0,85
Servo:1,130
Servo:2,21
...
```

Python parses these and updates the shared `servo_angles` dictionary, which the Flask server then exposes to the browser dashboard. This is the backbone of the real-time visualisation — the dashboard always shows what the physical arms are actually doing, not a simulated guess.

During `coordinatedMove()`, telemetry is optimised: only the **active joints** are broadcast per micro-step (not all 16), reducing serial bottleneck during high-frequency motion. A full `broadcastAngles()` call runs at the end of each phase to resynchronise.

---

## 8. Python Middleware — How the Three Threads Work

### Why Threads?

The Python application needs to do three things simultaneously:
1. Read from the serial port continuously (or it fills up and data is lost)
2. Host a Flask web server (so the browser can poll for data)
3. Play audio announcements (which can take 2–4 seconds each)

If these ran sequentially, audio playback would block serial reading — telemetry would pile up in the buffer, and the dashboard would freeze until the audio finished. The solution is three concurrent threads sharing the same memory.

### Thread Architecture

```
┌─────────────────────────────────────────────────────────┐
│ MAIN THREAD                                             │
│   Handles terminal input (run / exit)                   │
│   Pushes 'run' command into cmd_queue deque             │
│   Coordinates blocking audio at mission complete        │
└─────────────────────────┬───────────────────────────────┘
                          │ cmd_queue (thread-safe deque)
┌─────────────────────────▼───────────────────────────────┐
│ SERIAL THREAD (daemon)                                  │
│   Opens serial port, sends knock, waits for handshake   │
│   Drains ser.in_waiting in tight loop (5ms sleep)       │
│   Parses "Servo:pin,angle" → updates servo_angles{}     │
│   Parses "Action:label" → triggers speak() + logs       │
│   Calls update_trajectory() after each angle update     │
└─────────────────────────┬───────────────────────────────┘
                          │ shared servo_angles{}, trajectory{}
                          │ protected by trajectory_lock
┌─────────────────────────▼───────────────────────────────┐
│ FLASK THREAD (daemon)                                   │
│   Serves HTTP endpoints on 127.0.0.1:5001               │
│   GET /data       → {angles, action}                    │
│   GET /trajectory → {t[], left_gripper[], right_gripper[]} │
│   GET /metrics    → {elapsed, samples, distances}       │
└─────────────────────────────────────────────────────────┘
```

### The speak_lock

```python
speak_lock = threading.Lock()

def speak(filename=None, fallback_text=None, blocking=False):
    def _speak():
        with speak_lock:           # Only one audio thread can hold this at a time
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
```

If the Arduino sends two `Action:` messages close together, without the lock, two audio files could play simultaneously. The lock ensures they queue naturally — the second waits until the first finishes.

### The Serial Buffer Drain Fix

During the coordinated task, the LERP engine sends telemetry much faster than the handover task (every micro-step across 90 steps). Early testing showed audio lagging 3–4 seconds behind the physical motion.

**Root cause:** Python was calling `ser.readline()` once per loop iteration. As telemetry arrived faster than it was being consumed, the buffer filled up. When an `Action:` message arrived, it sat in the buffer behind hundreds of unread `Servo:` lines.

**Fix:**

```python
# BEFORE (slow — reads one line per loop iteration):
while active:
    line = ser.readline()
    process(line)
    time.sleep(0.01)

# AFTER (fast — drains entire buffer before sleeping):
while active:
    while ser.in_waiting > 0:        # Keep reading until buffer is empty
        line = ser.readline()
        process(line)
    time.sleep(0.005)                # Then yield for 5ms
```

This ensures `Action:` messages are processed within milliseconds of the Arduino sending them, even during high-frequency telemetry phases.

---

## 9. Forward Kinematics — The Mathematics

### What is Forward Kinematics?

Forward kinematics (FK) answers the question: **given the angle of every joint, where is the gripper tip in 3D space?**

It is called "forward" because it works in the natural direction: joints → position. The reverse problem (given a desired position, find the joint angles) is **inverse kinematics** (IK) and is significantly harder to solve. This project uses FK only.

### Why is FK Needed?

The raw servo angles (e.g., "joint 2 is at 130°") are not intuitively meaningful for visualisation or analysis. FK converts them into Cartesian coordinates (x, y, z) which can be:
- Plotted on a graph to show how far the arm reached over time
- Used to compute the distance between two gripper tips
- Displayed as a 3D animated model in the browser

### The FK Model Used

This project uses a **vector-geometric** FK approach rather than the full Denavit-Hartenberg (DH) matrix method. Each joint's contribution to the end-effector position is computed as a sequential chain of unit vectors scaled by link lengths.

**Step 1: Convert joint angles to deltas from home**

At home position, the arm is in its neutral vertical configuration. Expressing angles as deltas from home means:
- δ = 0 → joint is at home (no contribution to deviation)
- δ > 0 → joint has moved forward from home
- δ < 0 → joint has moved backward from home

```python
delta_shoulder = (shoulder_angle - HOME_shoulder) / 90.0
```

Dividing by 90 normalises the range so that a 90° movement from home produces a delta of 1.0 — a convenient scale for the trigonometric calculations.

**Step 2: Compute the base rotation angle**

```python
base_rad = ((base_angle - HOME_base) / 90.0) * (pi * 0.5)
```

This maps the base servo's angular delta to a horizontal rotation angle in radians. The factor 0.5 (= π/2 ÷ π) gives approximately 90° of physical arm swing per 90° of servo travel.

**Step 3: Chain the joint directions**

Starting from the base top position, each joint's contribution is computed as a direction unit vector multiplied by that link's length:

```python
# Shoulder direction vector (unit vector pointing from base top toward elbow)
shoulder_dir = normalize((
    sin(base_rad) * sin(shoulder_tilt),  # x component
    cos(shoulder_tilt),                   # y component (vertical)
    cos(base_rad) * sin(shoulder_tilt)    # z component
))

# Elbow position = base top + (shoulder direction × upper arm length)
elbow_pos = base_top + shoulder_dir × 2.0
```

This repeats for each subsequent joint, with cumulative tilt angles:

```
cumulative_tilt = shoulder_tilt + elbow_tilt
```

The cumulative tilt ensures each distal joint's direction is expressed relative to the global reference frame, not just relative to the previous joint.

**Step 4: Full FK chain**

```
base_top  = (offset_x, 0.6, 0.0)                     [fixed base pedestal]
elbow_pos = base_top + shoulder_dir × 2.0             [upper arm]
wrist_pos = elbow_pos + elbow_dir × 1.6               [forearm]
gripper   = wrist_pos + wrist_dir × 0.8               [wrist extension]
```

The formal vector-summation expression:

```
X = Σᵢ Lᵢ · cos(Σⱼ₌₁ⁱ θⱼ)
Y = Σᵢ Lᵢ · sin(Σⱼ₌₁ⁱ θⱼ)
```

Where Lᵢ are link lengths and θⱼ are cumulative joint angles.

### Same Math in Two Places

The Python middleware and the JavaScript dashboard run **identical FK calculations**. This is essential: if they differed, the 3D browser visualisation would show different arm positions from what the Python telemetry was recording — making the trajectory charts and 3D model inconsistent.

---

## 10. Inter-Gripper Distance — The Synchronisation Proof

### The Formula

Once both gripper tip positions are known in 3D space:

```
Left gripper:  (xL, yL, zL)
Right gripper: (xR, yR, zR)

D_separation = √( (xL−xR)² + (yL−yR)² + (zL−zR)² )
```

This is the standard **3D Euclidean distance** formula.

### Why This Metric Matters

During the synchronised pick-and-place task, both grippers are holding the same rigid object. If the arms are perfectly synchronised:
- Both grippers move at the same velocity
- Their relative distance stays constant
- `D_separation` is flat

If there is any timing mismatch:
- One arm moves faster or arrives earlier
- The grippers try to pull the object apart
- `D_separation` fluctuates — visible as a wavy line on the chart

The **flat line during the hold phase** in Chart 3 of the dashboard is therefore the single strongest evidence of successful synchronisation. Mathematically, it demonstrates:

```
dD_separation/dt = 0    during the bilateral hold phase
```

### Distance From Base

A secondary metric — how far each gripper has reached from its own base pivot:

```python
def _distance_from_base(grip_xyz, origin_x):
    dx = grip_xyz[0] - origin_x   # horizontal offset from base centre
    return sqrt(dx² + y² + z²)
```

For the left arm, `origin_x = -4.0`; for the right arm, `origin_x = +4.0` (in scene units). During the approach phase, both arms reach out, so this value rises. During lift, they shorten. The parallel rise and fall of both traces on Charts 1 and 2 confirms the arms moved at matching velocities.

---

## 11. The Browser Dashboard — 3D Visualisation and Charts

### Three.js Particle Arm Rendering

Each arm is rendered as a cloud of **130 glowing particles** rather than solid geometry. This was a deliberate aesthetic and technical choice:
- Additive blending (`THREE.AdditiveBlending`) makes overlapping particles glow brighter, creating a natural depth cue
- Particles are computationally cheaper than mesh geometry for a real-time application
- The glowing effect better communicates the "active mechanical system" aesthetic

Particle positions are computed from the FK arm keypoints:

```javascript
function buildArmPoints(kp) {
    const pts = [];
    // Evenly space particles along each arm segment
    addSegment(kp.origin,   kp.baseTop,  4 particles);
    addSegment(kp.baseTop,  kp.elbowPos, 12 particles);
    addSegment(kp.elbowPos, kp.wristPos, 10 particles);
    addSegment(kp.wristPos, kp.clawBase, 5 particles);
    addSegment(kp.clawBase, kp.prong1,   4 particles);  // Gripper prong 1
    addSegment(kp.clawBase, kp.prong2,   4 particles);  // Gripper prong 2
    // Plus 24 particles in a ring at the base, and scatter at joints
}
```

### Display LERP — Why the Animation Is Smooth

The Flask server updates servo angles at ~10Hz (100ms polling). If the 3D model snapped instantly to each new value, the animation would look jerky and robotic. Instead, the display angles are smoothed using exponential decay interpolation:

```javascript
// Each animation frame:
const smoothing = 1 - Math.exp(-8 * delta);   // dashboard_3 (handover)
// const smoothing = 1 - Math.exp(-40 * delta);  // dashboard_4 (coordinated, faster)

currentDisplayAngles[pin] += (targetAngles[pin] - currentDisplayAngles[pin]) * smoothing;
```

**How this works:**
- `targetAngles[pin]` = the real angle from the Flask server (steps discretely)
- `currentDisplayAngles[pin]` = the smoothed display angle (changes every frame)
- The display angle moves toward the target at a rate proportional to their difference

With `exp(-8 * delta)` at 60fps (delta ≈ 0.017s): `smoothing ≈ 0.128` — the display angle closes ~12.8% of the remaining gap each frame, giving smooth motion.

Dashboard 4 uses a higher factor (`-40`) because the coordinated task's LERP firmware already moves smoothly — the display needs to track more tightly to stay accurate.

### Recursive setTimeout vs setInterval

Dashboard 3 uses `setInterval(pollFlask, 33)` — a fixed 33ms interval between poll start times.

Dashboard 4 uses recursive `setTimeout`:

```javascript
async function pollFlask() {
    // ... fetch and process data ...
    setTimeout(pollFlask, 16);  // Schedule next call AFTER this one completes
}
pollFlask();  // Start the chain
```

During high-frequency LERP telemetry (coordinatedMove sends data every 13ms), `setInterval` can cause requests to queue up because a new request starts before the previous response arrives. Recursive `setTimeout` prevents this — each new request only starts after the previous one has fully resolved, eliminating network backup.

### The Four Charts Explained

| Chart | Y-axis | What it shows |
|-------|--------|---------------|
| Left gripper distance from base | Scene units | How far left arm has extended; rises on approach, falls on lift |
| Right gripper distance from base | Scene units | Same for right arm; should mirror left in coordinated task |
| Inter-gripper separation | Scene units | Closes during approach/grab; flat during hold (sync proof) |
| Gripper vertical (scene Y) | Scene units | Height of each gripper; both rise together during lift |

### Coordinated Dashboard Exclusive Features

**SYNCHRONISED PICK badge:** Fades in when `current_action` contains "Both arms" or "Holding". Uses CSS opacity transition:

```css
#sync-badge { opacity: 0; transition: opacity .4s; }
#sync-badge.visible { opacity: 1; }
```

```javascript
syncBadge.classList.toggle('visible', isSyncMode);
```

**Amber gripper glow:** A `THREE.Mesh` sphere (colour 0xffaa00, additive blending) is positioned at each gripper's `clawBase` point. Its opacity is set to a function of how closed the gripper is × whether `isGripping` is true:

```javascript
const gripFrac = Math.max(0, 1 - kp.clawAngle / 20);  // 1 = fully closed
obj.gripGlow.material.opacity = isGripping ? gripFrac * 0.55 : 0;
```

**Amber inter-gripper bar:** The CSS class `gripping` is toggled during bilateral hold phases, changing the bar colour:

```css
.dist-meter-fill.inter.gripping {
    background: linear-gradient(90deg, #ff6600, #ffcc00);
    box-shadow: 0 0 6px #ffaa00;
}
```

---

## 12. Audio System Design

### Handover Task — ElevenLabs Pre-generated MP3

The handover task uses ElevenLabs cloud TTS to generate high-quality British-accent audio files using the "George" voice — selected because it closely matches the J.A.R.V.I.S. character from Iron Man. All files were generated in advance and stored locally as 192kbps MP3 files.

Playback uses macOS `afplay`:

```python
subprocess.run(['afplay', os.path.join(AUDIO_DIR, filename)])
```

Pre-generating the files eliminates:
- Internet dependency during demonstrations
- API credit consumption on each run
- Variable latency from cloud TTS requests

Fallback to macOS `say` command (Daniel voice) if any file is missing.

### Coordinated Task — macOS Samantha TTS

The coordinated task uses the macOS Samantha voice (F.R.I.D.A.Y. aesthetic) at 180 words-per-minute:

```python
subprocess.run(['say', '-v', 'Samantha', '-r', '180', text])
```

This approach requires no pre-generated files, making the coordinated task fully offline and portable without the JARVIS_Audio folder.

### Audio-to-Motion Synchronisation

Each `Action:` message from the Arduino arrives just **before** the corresponding physical motion begins. The timing buffer in the firmware:

```cpp
Serial.println("Action: Both arms approaching");
delay(1200);                               // Speech setup time
coordinatedMove(armPins, pickTargets, ...);  // Physical motion starts
```

The 1200ms delay gives the Python `speak()` thread time to begin playing audio before the arms start moving, so the narration aligns with the physical action.

---

## 13. Key Engineering Findings

### Finding 1: Voltage, Not Current, Is the Limiting Factor

The original assumption was that servo stall current (1.8A per DM996/MG996R) would be the primary constraint — suggesting a high-current power supply was needed. A 5V/15A supply was purchased.

In practice:
- Idle current per servo: ~0.1A
- Active movement: 0.3–0.8A
- Peak (all 12 moving): ~2.60A

The 5V/15A supply had more than enough current, but the servos would not complete their full range of motion because the voltage was too low. The DM996 is specified for 6–7.4V. At 5V, the magnetic torque generated by the motor windings was insufficient to overcome gravitational load on the extended arm.

**Engineering lesson:** Always check the operating voltage range of actuators, not just the current rating. A high-current supply at the wrong voltage is useless.

### Finding 2: Float vs Integer in LERP

Integer arithmetic in the interpolation step loop caused joint-arrival ordering errors in the synchronised task. When moving a joint only 9° over 90 steps, the integer increment is truncated to 0 — the joint never moves, or arrives at completely the wrong time relative to other joints.

Using `float` throughout the LERP engine eliminated this entirely. The physical evidence: the payload remained level throughout the lift, and the inter-gripper distance chart showed a perfectly flat hold phase.

### Finding 3: Infill Density vs Servo Load

At 15% Gyroid infill, the structural arm components were light enough that the shoulder servo could complete a full 130° sweep under load. Testing indicated that higher infill densities (30%+) would significantly increase servo loading, likely causing stall conditions at 6.8V.

Gears required separate treatment — they needed 40–45% infill to prevent tooth deformation under cyclic loading. This required printing them separately at a slower speed (20–30mm/s).

### Finding 4: Wire Management in the Base Joint

When the left arm base rotates to 172°, the jumper wires routed through joints 2–6 resist the rotation, reducing the effective servo travel. This created intermittent repeatability failures. The fix was to bundle and tape all wires to one side of the shoulder section — eliminating the mechanical resistance.

**Engineering lesson:** Cable management in rotating joints is not cosmetic. Uncontrolled wire routing introduces variable mechanical loads that software cannot compensate for.

### Finding 5: Serial Buffer Drain

High-frequency serial telemetry from the LERP engine caused audio announcements to lag 3–4 seconds behind physical motion. Root cause: Python's line-by-line serial reading could not keep up with the Arduino's output rate, causing `Action:` messages to queue behind hundreds of `Servo:` lines.

Fix: drain the entire `ser.in_waiting` buffer in each iteration rather than reading one line per loop cycle. Result: audio fired within milliseconds of the corresponding physical action.

---

## 14. What Could Be Improved

### Quantitative Results

The report qualitatively describes successful task completion, but does not report:
- Number of trials run (N)
- Success rate as X/N fraction
- Mean gripper position error in physical millimetres
- Standard deviation of repeatability across runs

The telemetry system was logging 5,000 timestamped entries per run. Statistical analysis of these logs would have provided the quantitative evidence the project lacked.

### Closed-Loop Control

The system is entirely **open-loop**: the Arduino commands a position and assumes the servo reached it. No sensor measures whether the servo actually arrived. Mechanical backlash, thermal drift in plastic gear housings, and PWM jitter all cause the physical position to deviate from the commanded position — observed as ~10–20mm repeatability variation between runs.

Adding magnetic absolute encoders at each joint would allow the firmware to measure and correct positional drift in real-time.

### Denavit-Hartenberg FK

The vector-geometric FK model is a reasonable approximation but not a rigorous implementation. The DH parameter approach uses homogeneous transformation matrices:

```
T = Rz(θ) · Tz(d) · Tx(a) · Rx(α)
```

Where θ, d, a, α are the four DH parameters per joint. This would enable true inverse kinematics — commanding the gripper to a Cartesian position and having the firmware solve for the required joint angles automatically, rather than using pre-programmed angle arrays.

### WebSocket Instead of HTTP Polling

The dashboard polls `/data` every 33ms. HTTP polling has overhead per request (TCP handshake, HTTP headers, JSON parsing). A WebSocket connection would maintain a persistent bidirectional channel, reducing latency and enabling the server to push updates as they arrive rather than waiting for a poll.

### Isolated Power Topology

During the synchronised lift, voltage needed to increase to 7.0V to overcome stall conditions. At 7.0V on a shared power rail, the PCA9685 logic supply (VCC, rated 6.0V max) was at risk. A custom PCB with separate regulated 5V and 7.4V rails — with the 7.4V rail supplying servo motors only and the 5V rail supplying all logic — would eliminate this risk and allow sustained operation at higher voltages.

---

*This document covers every significant technical aspect of the J.A.R.V.I.S. dual-arm robotic system. For quick-start instructions, see the main README. For hardware wiring, see HARDWARE.md. For joint calibration tables, see CALIBRATION.md. For FK equations, see KINEMATICS.md.*
