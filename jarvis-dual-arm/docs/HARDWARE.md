# Hardware Guide

## Mechanical Design

Each arm is based on the **FABRI CREATOR 6-DOF** design (Cults3D), comprising six joints:

| Joint # | Joint Name | Servo Model | Role |
|---------|------------|-------------|------|
| 1 | Base | DM996 | Full arm rotation (0–170°) |
| 2 | Shoulder | DM996 | Primary load-bearing |
| 3 | Elbow | MG996R | Secondary structural |
| 4 | Wrist Roll | SG90 | Light distal joint |
| 5 | Wrist Pitch | SG90 | Light distal joint |
| 6 | Gripper | SG90 | Object grasping (0–90°) |

The left and right arms are printed as mirror images and mounted **570 mm apart** (measured between base rotation centres). This spacing was determined empirically by positioning both arms at their handover extension angles and confirming clearance between grippers at the intended handover point.

---

## 3D Printing Settings

| Component Type | Infill | Layer Height | Notes |
|----------------|--------|--------------|-------|
| Structural parts (arms, base) | 15% Gyroid | 0.2 mm | 4–6 wall loops; tree supports on overhangs |
| Precision parts (gears, central shaft) | 40–45% | 0.15 mm | 20–30 mm/s print speed; tooth accuracy critical |
| Prototype prints | 15% Gyroid | 0.2 mm | Used for fastener characterisation before final build |

**Printer:** Bambu Lab P2S  
**Filament:** PLA Matte (Textured PEI build plate; no warping)  
**Colours:** White + Blue (final), Black + Orange (prototype)

### STEP → STL Conversion
FABRI CREATOR STEP files were converted to STL format in **Autodesk Fusion 360**. A cable-routing aperture was added to the base enclosure rear to route jumper wires cleanly to the PCA9685 without mechanical stress on connectors during arm rotation.

---

## Fastener Specification

Identified during prototype assembly phase (advised by Omar Dawaba, Jennison makerspace mechanic):

| Fastener | Size | Application |
|----------|------|-------------|
| Self-tapping screw | M2 × 8 mm | Small joint connections |
| Self-tapping screw | M2.2 × 4.5 mm | Thin section closures |
| Self-tapping screw | M2.2 × 8 mm | Mid-section body |
| Nut + washer | M3 | Load-bearing connections |
| Pan Pozi screw | M3 × 6 mm | General assembly |
| Pan Pozi screw | M3 × 12 mm | Longer reach assembly |
| Countersunk screw | M3 × 10 mm | Flush-mount applications |

**Tightening standard:** Finger-tight plus quarter-turn.  
- Under-tightening → servo horn slips under load  
- Over-tightening → horn binds on gear case, preventing smooth rotation

**Metal servo horns** were used wherever available. Plastic horns on the DM996/MG996R are susceptible to wear under cyclic loading — two horns on the prototype showed early thread wear and were replaced before the final build.

---

## Electronics Wiring

### I2C Connection (Arduino → PCA9685)

```
Arduino UNO R4 WiFi    PCA9685
─────────────────────────────────
A4 (SDA)         ──►  SDA
A5 (SCL)         ──►  SCL
5V               ──►  VCC  (logic supply)
GND              ──►  GND
```

### Power Supply Connection

```
GW Instek GPS-3303
─────────────────────────────────
CH1: 6.7V–6.8V / 3.0–3.12A  ──►  PCA9685 V+ (servo power rail)
GND                           ──►  PCA9685 GND
```

**Do not connect servo power rail (V+) to Arduino 5V.** The Arduino 5V rail cannot supply the current required for 12 servos.

### PCA9685 Channel Allocation

```
Channels 0–5:   Left Arm
  Ch 0  → L-Base        (DM996)
  Ch 1  → L-Shoulder    (DM996)
  Ch 2  → L-Elbow       (MG996R)
  Ch 3  → L-Wrist Roll  (SG90)
  Ch 4  → L-Wrist Pitch (SG90)
  Ch 5  → L-Gripper     (SG90)

Channels 6–9:   UNUSED

Channels 10–15: Right Arm
  Ch 10 → R-Base        (DM996)
  Ch 11 → R-Shoulder    (DM996)
  Ch 12 → R-Elbow       (MG996R)
  Ch 13 → R-Wrist Roll  (SG90)
  Ch 14 → R-Wrist Pitch (SG90)
  Ch 15 → R-Gripper     (SG90)
```

---

## Power Supply Findings

| Voltage | Behaviour |
|---------|-----------|
| 5.0V | DM996 fails to complete shoulder raise at full extension |
| 6.6V | Borderline — occasional stall under combined load |
| 6.8V | Reliable operation for all handover task movements |
| 7.0V | Required for synchronised bilateral lift; keep runs short |

**Current draw (measured):**
- Idle: ~0.1A per servo
- Active movement: 0.3–0.8A per servo
- Peak (12 servos, synchronised lift): ~2.60A

The theoretical simultaneous stall current (1.8A × 12 = ~21.6A) is a worst-case design figure, not representative of normal operation.

**⚠️ PCA9685 voltage limit:** The logic supply VCC is rated to 6.0V maximum. At 7.0V on a shared rail, restrict demonstration duration to protect the IC.

---

## Safety Incident Record

During an early power-on test, a DC bridge adapter borrowed from the Jennison laboratory emitted smoke when connected to the COOLM 5V/15A supply. The system was immediately powered down and the incident was reported to laboratory technicians and Ryan Morrow (Mechanical Engineering Officer) in accordance with school safety procedures. The incident was attributed to the adapter's current rating being insufficient for the load. The GW Instek GPS-3303 laboratory supply was used for all subsequent work. No injury occurred.
