// ============================================================
// EENG6010 — Coordinated Control of Robot Arms
// Prototype / Development Test Sketch
// University of Kent
//
// Early prototype sketch used during development to verify
// the coordinatedMove() LERP engine before integration with
// the full Python middleware and dashboard pipeline.
//
// Runs standalone — no handshake, no Flask server required.
// Flash and use Arduino IDE Serial Monitor. Type "test" to run.
//
// This is the initial fixed version that resolved the global
// pin definition error present in early development builds.
// ============================================================

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

#define SERVO_FREQ  50
#define BIG_MIN    130
#define BIG_MAX    600
#define SMALL_MIN  150
#define SMALL_MAX  550

// Global pin groups
int armPins[]     = {0, 1, 2, 3, 4, 10, 11, 12, 13, 14};
int gripperPins[] = {5, 15};
int numArmServos  = 10;
int numGripServos = 2;

// Current angles as floats for smooth math
float currentAngles[16] = {85, 90, 91, 96, 90, 90, 0, 0, 0, 0, 93, 90, 90, 92, 90, 90};

// Forward declarations
void setAngle(int pin, float angle);
void coordinatedMove(int pins[], int targets[], int numServos, int durationMs);
void executeFullCycle();

void setup() {
  Serial.begin(115200);
  pwm.begin();
  pwm.setPWMFreq(SERVO_FREQ);

  for (int i = 0; i < 16; i++) { setAngle(i, currentAngles[i]); }

  Serial.println("--- PROTOTYPE TEST SKETCH ---");
  Serial.println("Type 'test' to begin.");
}

void loop() {
  if (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd == "test") executeFullCycle();
  }
}

// ============================================================
// coordinatedMove — 50-step LERP (prototype version)
// Note: Production version uses MOVE_STEPS = 90
// ============================================================
void coordinatedMove(int pins[], int targets[], int numServos, int durationMs) {
  int steps     = 50;
  int stepDelay = durationMs / steps;

  float startAngles[12];
  float increments[12];

  for (int i = 0; i < numServos; i++) {
    int p          = pins[i];
    startAngles[i] = currentAngles[p];
    increments[i]  = (float)(targets[i] - startAngles[i]) / steps;
  }

  for (int s = 1; s <= steps; s++) {
    for (int i = 0; i < numServos; i++) {
      int p = pins[i];
      currentAngles[p] = startAngles[i] + (increments[i] * s);
      setAngle(p, currentAngles[p]);
    }
    delay(stepDelay);
  }
}

void executeFullCycle() {
  // 1. APPROACH
  Serial.println("1/5: Coordinated Approach...");
  int pickTargets[] = {85, 130, 21, 0, 91, 93, 130, 21, 0, 90};
  coordinatedMove(armPins, pickTargets, numArmServos, 1300);
  delay(1500);

  // 2. GRAB
  Serial.println("2/5: Synchronized Grab...");
  int grabTargets[] = {0, 0};
  coordinatedMove(gripperPins, grabTargets, numGripServos, 800);
  delay(1500);

  // 3. LIFT
  Serial.println("3/5: Smooth Lift...");
  int homeTargets[] = {85, 90, 93, 0, 91, 93, 90, 90, 0, 90};
  coordinatedMove(armPins, homeTargets, numArmServos, 1300);
  delay(1500);

  // 4. PLACE
  Serial.println("4/5: Moving to Place Position...");
  int placeTargets[] = {85, 130, 21, 0, 91, 93, 130, 21, 0, 90};
  coordinatedMove(armPins, placeTargets, numArmServos, 1300);
  delay(1500);

  // 5. RELEASE & RESET
  Serial.println("5/5: Release and Reset...");
  int releaseTargets[] = {90, 90};
  coordinatedMove(gripperPins, releaseTargets, numGripServos, 600);
  delay(300);
  coordinatedMove(armPins, homeTargets, numArmServos, 1100);

  Serial.println("--- Mission Complete ---");
}

void setAngle(int pin, float angle) {
  int pulse;
  if ((pin >= 0 && pin <= 2) || (pin >= 10 && pin <= 12)) {
    pulse = map((int)angle, 0, 180, BIG_MIN, BIG_MAX);
  } else {
    pulse = map((int)angle, 0, 180, SMALL_MIN, SMALL_MAX);
  }
  pwm.setPWM(pin, 0, pulse);
}
