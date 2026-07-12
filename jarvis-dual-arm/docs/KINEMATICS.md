# Kinematics Reference

## Coordinate System

The workspace coordinate system is defined with:
- **Origin:** Midpoint between the two arm base centres
- **Left arm base:** x = −4.0 (scene units)
- **Right arm base:** x = +4.0 (scene units)
- **Y-axis:** Vertical (upward positive)
- **Z-axis:** Depth

Physical arm segment lengths used in the model:

| Segment | Scene Units |
|---------|-------------|
| Base pedestal | 0.6 |
| Upper arm (shoulder → elbow) | 2.0 |
| Forearm (elbow → wrist) | 1.6 |
| Wrist extension (wrist → claw base) | 0.8 |

---

## Forward Kinematics

Gripper tip position (X, Y, Z) is computed from joint angles using vector-geometric forward kinematics. This is implemented identically in both the Python middleware and the browser dashboard to keep both in sync.

### Formulation

For an n-joint arm with link lengths L₁, L₂, ..., Lₙ and joint angles θ₁, θ₂, ..., θₙ:

```
X = Σ Lᵢ · cos(Σⱼ₌₁ⁱ θⱼ)
Y = Σ Lᵢ · sin(Σⱼ₌₁ⁱ θⱼ)
```

Joint angles are expressed as deltas from their home positions:

```
δᵢ = (currentAngle - homeAngle) / 90
```

This ensures that at home position, δ = 0 and the arm is in its neutral vertical configuration.

### Python Implementation

```python
def compute_gripper_position(pins, offset_x):
    base_rad     = ((servo_angle(p[0]) - HOME[p[0]]) / 90.0) * (math.pi * 0.5)
    shoulder_tilt = ((servo_angle(p[1]) - HOME[p[1]]) / 90.0) * math.pi * 0.75
    elbow_tilt    = -((servo_angle(p[2]) - HOME[p[2]]) / 90.0) * math.pi * 0.65
    wrist_tilt    = -((servo_angle(p[4]) - HOME[p[4]]) / 90.0) * math.pi * 0.30

    # Chain joint positions along cumulative tilt direction
    shoulder_dir = normalize((sin(base_rad)*sin(shoulder_tilt),
                               cos(shoulder_tilt),
                               cos(base_rad)*sin(shoulder_tilt)))
    elbow_pos    = base_top + shoulder_dir * 2.0

    cumul_tilt   = shoulder_tilt + elbow_tilt
    elbow_dir    = normalize((sin(base_rad)*sin(cumul_tilt), ...))
    wrist_pos    = elbow_pos + elbow_dir * 1.6

    wrist_cum_tilt = cumul_tilt + wrist_tilt
    wrist_dir    = normalize((sin(base_rad)*sin(wrist_cum_tilt), ...))
    return wrist_pos + wrist_dir * 0.8
```

---

## Inter-Gripper Distance (Synchronisation Metric)

The primary success metric for the coordinated pick-and-place task. Computed in real-time from the gripper tip positions:

```
D_separation = √( (xL−xR)² + (yL−yR)² + (zL−zR)² )
```

Where (xL, yL, zL) and (xR, yR, zR) are the left and right gripper tip positions respectively.

**Interpretation:**
- A **decreasing** value indicates the arms are converging
- A **flat, constant** value during the hold phase (`dD/dt = 0`) confirms perfect bilateral synchronisation — the relative distance between grippers did not change, proving no timing lag or speed mismatch
- An **increasing** value indicates the arms are separating (release / homing phase)

---

## LERP Motion Engine

The `coordinatedMove()` function implements parametric joint-space linear interpolation (LERP) across a fixed number of steps:

```
θᵢ(s) = θᵢ_start + (θᵢ_target − θᵢ_start) · (s / MOVE_STEPS)
```

Where:
- `θᵢ_start` = initial angle of servo i at step 0
- `θᵢ_target` = destination angle of servo i
- `s` = current step index (1 ≤ s ≤ MOVE_STEPS)
- `MOVE_STEPS = 90` (global constant)

The uniform time interval between steps:

```
Δt = durationMs / MOVE_STEPS
```

**Critical implementation detail:** Increments must be computed as `float`, not `int`. Integer truncation causes joints with shorter travel distances to arrive before joints with longer distances (step aliasing), producing mechanical shear on a jointly-held payload. The `float` LERP engine ensures all joints begin and complete their travel at the exact same millisecond regardless of travel distance.

---

## Dashboard 3D Visualisation (Three.js)

The browser dashboard mirrors the Python FK model in JavaScript. A separate LERP layer is applied to display angles to smooth the discrete servo steps for visual presentation:

```javascript
// Smooth display angles toward real target angles each frame
const smoothing = 1 - Math.exp(-8 * delta);   // dashboard_3
// const smoothing = 1 - Math.exp(-40 * delta); // dashboard_4 (faster response)

currentDisplayAngles[pin] += (targetAngles[pin] - currentDisplayAngles[pin]) * smoothing;
```

This ensures the 3D particle animation appears fluid even though the servo telemetry arrives in discrete steps at 100ms intervals.

---

## Limitations

This implementation uses a vector-geometric approximation of forward kinematics rather than a full Denavit-Hartenberg (DH) homogeneous transformation matrix approach. Consequences:

- The FK model is a reasonable approximation for visualisation but does not account for all joint interaction effects
- Inverse kinematics (IK) path planning cannot be implemented without DH parameters
- The gripper tip position in scene units is not directly convertible to physical millimetres without a measured scale factor

Future work: Implementing the full DH parameter approach would enable dynamic spatial targeting rather than pre-programmed joint angle arrays.
