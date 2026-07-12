// ============================================================
// EENG6010 — Coordinated Control of Robot Arms
// Coordinated Pick-and-Place Firmware
// University of Kent
//
// Performs a synchronised bilateral pick-and-place operation:
//   Both arms approach → grip → lift → hold → lower → release → home
//
// Motion profile: coordinatedMove() — LERP-based multi-joint interpolation
//   All joints begin and finish at the exact same millisecond regardless
//   of travel distance. Float arithmetic required — int truncation causes
//   joint-arrival ordering errors and mechanical shear.
//
// Serial commands:  "test"  → executeFullCycle()
// ============================================================

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

#define SERVO_FREQ   50
#define BIG_MIN     130    // DM996 / MG996R: Base, Shoulder, Elbow (pins 0-2, 10-12)
#define BIG_MAX     600
#define SMALL_MIN   150    // SG90: Wrist Roll, Wrist Pitch, Gripper (pins 3-5, 13-15)
#define SMALL_MAX   550
#define MOVE_STEPS   90    // Steps per coordinatedMove() — higher = smoother
#define MAX_SERVOS   12    // Max pins in one coordinatedMove() call

// ============================================================
// PIN GROUPS
// ============================================================
int armPins[]       = {0, 1, 2, 3, 4, 10, 11, 12, 13, 14};
int gripperPins[]   = {5, 15};
int wristRollPins[] = {3, 13};   // Restored to home at end of cycle

// ============================================================
// HOME POSITIONS (float array — required for LERP arithmetic)
// ============================================================
float currentAngles[16] = {
   85,  90,  91,  96,  90,  90,   // pins  0-5  (left arm)
    0,   0,   0,   0,             // pins  6-9  (unused)
   93,  90,  90,  92,  90,  90   // pins 10-15 (right arm)
};

// ============================================================
// SEQUENCE ANGLE TABLES
// ============================================================
int pickTargets[]  = {85, 130, 22, 96, 43,  93, 130, 22, 92, 43};
int liftTargets[]  = {85,  90, 91, 96, 90,  93,  90, 90, 92, 90};
int wristHomeT[]   = {96, 92};    // left wrist roll home, right wrist roll home

// ============================================================
// SETUP
// ============================================================
void setup() {
  Serial.begin(115200);
  pwm.begin();
  pwm.setPWMFreq(SERVO_FREQ);

  // Drive servos to safe home positions
  for (int i = 0; i < 16; i++) { setAngle(i, currentAngles[i]); }

  // Knock-knock handshake — hold until Python sends knock byte
  while (Serial.available() <= 0) { delay(500); }
  while (Serial.available() > 0)  { Serial.read(); }  // flush

  broadcastAngles();
  Serial.println("Action: System Ready");
}

// ============================================================
// LOOP — command dispatcher
// ============================================================
void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "test") {
      executeFullCycle();
    }
  }
}

// ============================================================
// setAngle — drives a servo and updates currentAngles[]
// ============================================================
void setAngle(int pin, float angle) {
  bool isBig = ((pin >= 0 && pin <= 2) || (pin >= 10 && pin <= 12));
  int  pulse  = isBig
                ? map((int)angle, 0, 180, BIG_MIN,   BIG_MAX)
                : map((int)angle, 0, 180, SMALL_MIN, SMALL_MAX);
  pwm.setPWM(pin, 0, pulse);
  if (pin >= 0 && pin < 16) currentAngles[pin] = angle;
}

// ============================================================
// broadcastAngles — streams all 16 servo positions over serial
// ============================================================
void broadcastAngles() {
  for (int i = 0; i < 16; i++) {
    Serial.print("Servo:");
    Serial.print(i);
    Serial.print(",");
    Serial.println((int)round(currentAngles[i]));
  }
}

// ============================================================
// coordinatedMove — LERP multi-joint synchronised engine
//
// All servos begin and arrive at their targets at the exact
// same millisecond. Float increments prevent joint-arrival
// ordering errors that occur with integer truncation.
//
// θᵢ(s) = θᵢ_start + (θᵢ_target − θᵢ_start) × (s / MOVE_STEPS)
// Δt    = durationMs / MOVE_STEPS
// ============================================================
void coordinatedMove(int* pins, int* targets, int numServos, int durationMs) {
  int stepDelay = max(1, durationMs / MOVE_STEPS);

  float startAngles[MAX_SERVOS];
  float increments[MAX_SERVOS];

  for (int i = 0; i < numServos; i++) {
    startAngles[i] = currentAngles[pins[i]];
    increments[i]  = (float)(targets[i] - startAngles[i]) / MOVE_STEPS;
  }

  for (int s = 1; s <= MOVE_STEPS; s++) {
    for (int i = 0; i < numServos; i++) {
      float angle = startAngles[i] + (increments[i] * s);
      setAngle(pins[i], angle);

      // Transmit only active joints each micro-step (reduces serial bottleneck)
      Serial.print("Servo:");
      Serial.print(pins[i]);
      Serial.print(",");
      Serial.println((int)round(angle));
    }
    delay(stepDelay);
  }
  broadcastAngles();  // Full broadcast at phase completion
}

// ============================================================
// SYNCHRONISED PICK-UP CYCLE
// ============================================================
void executeFullCycle() {

  // ── Phase 1: Approach — both arms reach down ─────────────────
  Serial.println("Action: Both arms approaching");
  delay(1200);   // Wait for speech phrase to begin
  coordinatedMove(armPins, pickTargets, 10, 1200);
  delay(2000);

  // ── Phase 2: Grip — both grippers close simultaneously ───────
  Serial.println("Action: Both arms grabbing");
  delay(1000);
  int grabTargets[] = {0, 0};
  coordinatedMove(gripperPins, grabTargets, 2, 1000);
  delay(1500);

  // ── Phase 3: Lift — both arms raise together ─────────────────
  Serial.println("Action: Both arms lifting");
  delay(1000);
  coordinatedMove(armPins, liftTargets, 10, 800);
  delay(1500);

  // ── Phase 4: Hold ─────────────────────────────────────────────
  Serial.println("Action: Holding position");
  delay(2500);

  // ── Phase 5: Lower — both arms descend simultaneously ────────
  Serial.println("Action: Both arms placing");
  delay(1000);
  coordinatedMove(armPins, pickTargets, 10, 1200);
  delay(1800);

  // ── Phase 6: Release — both grippers open simultaneously ──────
  Serial.println("Action: Both arms releasing");
  delay(1000);
  int releaseTargets[] = {90, 90};
  coordinatedMove(gripperPins, releaseTargets, 2, 600);
  delay(1500);

  // ── Phase 7: Home — two-step return ───────────────────────────
  Serial.println("Action: Homing both arms");
  delay(1200);
  coordinatedMove(armPins, liftTargets, 10, 800);         // Step A: arms up to clearance
  delay(1000);
  coordinatedMove(wristRollPins, wristHomeT, 2, 1000);    // Step B: restore wrist rolls
  delay(2000);

  Serial.println("Action: Mission complete");
}
