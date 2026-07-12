# Calibration Guide

## Pre-Assembly Servo Calibration

Every servo must be pre-set to **90°** using a dedicated calibration sketch before installation. A servo powered without first being positioned to its home angle will attempt to drive from an unknown starting position, placing excessive load on the gear train during start-up.

Flash the following to verify each servo before attaching to the arm:

```cpp
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

void setup() {
  pwm.begin();
  pwm.setPWMFreq(50);
  // Drive all channels to 90° (mid-point)
  for (int i = 0; i < 16; i++) {
    int pulse = map(90, 0, 180, 150, 550); // SMALL range — adjust per servo type
    pwm.setPWM(i, 0, pulse);
  }
}
void loop() {}
```

---

## Right Arm Joint Characterisation

The right arm was calibrated first and served as the baseline for left arm configuration.

| Pin | Joint | Home (°) | Range (°) | 0° Direction | 180° Direction |
|-----|-------|----------|-----------|--------------|----------------|
| 10 | R-Base | 93 | 0–170 | Left | Right |
| 11 | R-Shoulder | 90 | 0–155 | Backward | Forward |
| 12 | R-Elbow | 90 | 0–150 | Forward | Backward |
| 13 | R-Wrist Roll | 92 | 0–160 | Left | Right |
| 14 | R-Wrist Pitch | 90 | 0–150 | Backward | Forward |
| 15 | R-Gripper | 90 | 0–90 | Closed | Open |

## Left Arm Home Positions

| Pin | Joint | Home (°) |
|-----|-------|----------|
| 0 | L-Base | 85 |
| 1 | L-Shoulder | 90 |
| 2 | L-Elbow | 91 |
| 3 | L-Wrist Roll | 96 |
| 4 | L-Wrist Pitch | 90 |
| 5 | L-Gripper | 90 |

---

## PWM Pulse Width Mapping

Two mapping ranges are required because the DM996/MG996R and SG90 servos have different internal pulse thresholds despite sharing the same 50Hz frame:

| Servo Type | Pins | SERVOMIN | SERVOMAX |
|------------|------|----------|----------|
| DM996 / MG996R (large) | 0–2, 10–12 | 130 | 600 |
| SG90 (small) | 3–5, 13–15 | 150 | 550 |

```cpp
// In setAngle():
bool isBig = ((pin >= 0 && pin <= 2) || (pin >= 10 && pin <= 12));
int pulse = isBig
    ? map((int)angle, 0, 180, 130, 600)
    : map((int)angle, 0, 180, 150, 550);
```

These values were determined empirically. The manufacturer's published SERVOMIN/SERVOMAX values may differ from what your specific servo batch requires — always verify by commanding 0°, 90°, and 180° and confirming physical limits are not exceeded.

---

## Handover Task Angle Table

| Step | Action | Key Joint Angles |
|------|--------|-----------------|
| 1 | Left arm pick | Pin 5: 90° (open) → Pin 1: 130°, Pin 2: 21°, Pin 3: 96°, Pin 4: 44° → Pin 5: 0° (grip) |
| 2 | Centering | Pin 4: 90°, Pin 2: 97°, Pin 1: 90° |
| 3 | Rotate to handover | Pin 0: 172° |
| 4 | Extend left arm | Pin 1: 115°, Pin 2: 48°, Pin 4: 88° |
| 5 | Right arm receive | Pin 14: 89°, Pin 13: 0°, Pin 12: 42°, Pin 11: 115°, Pin 10: 18°, Pin 15: 5° → 0° |
| 6 | Left arm release | Pin 5: 90° |
| 7 | Right arm to drop zone | Pin 12: 90°, Pin 11: 90°, Pin 10: 93°, Pin 11: 130°, Pin 12: 21°, Pin 13: 92°, Pin 14: 44° |
| 8 | Final drop | Pin 15: 90° |
| 9 | Return home | homeLeft() + homeRight() |

> **Note on Step 3:** At 172°, wires routed through joints 2–6 may resist base rotation depending on cable management. Securing all wires to one side of the shoulder with tape resolved intermittent stalling in testing.

## Synchronised Pick-and-Place Angle Table

| Phase | Action | Key Targets | Duration |
|-------|--------|-------------|----------|
| 1 | Approach | Shoulder 130°, Elbow 22° (both arms) | 1200 ms lead + 1200 ms move |
| 2 | Grab | Grippers (Pins 5 & 15) → 0° | 1000 ms lead + 1000 ms move |
| 3 | Lift | Shoulder 90°, Elbow 91° (both arms) | 1000 ms lead + 800 ms move |
| 4 | Hold | All joints stationary | 2500 ms |
| 5 | Lower | Shoulder 130°, Elbow 22° (both arms) | 1000 ms lead + 1200 ms move |
| 6 | Release | Grippers (Pins 5 & 15) → 90° | 1000 ms lead + 600 ms move |
| 7 | Home | liftTargets[] then wristRollPins[] restore | 1200 ms lead + 800 ms move |
