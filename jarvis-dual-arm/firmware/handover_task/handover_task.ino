// ============================================================
// EENG6010 — Coordinated Control of Robot Arms
// Handover Task Firmware
// University of Kent
//
// Performs a sequential object handover:
//   Left arm picks → rotates → transfers to right arm → right arm drops
//
// Motion profile: smoothMove() — single-axis sequential steps
// Serial protocol: broadcastAngles() after every move
// Handshake: knock-knock — waits for Python 'k' byte before starting
//
// Serial commands:  "test"  → executeFullCycle()
// ============================================================

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

#define SERVO_FREQ  50
#define BIG_MIN    130    // DM996 / MG996R: Base, Shoulder, Elbow (pins 0-2, 10-12)
#define BIG_MAX    600
#define SMALL_MIN  150    // SG90: Wrist Roll, Wrist Pitch, Gripper (pins 3-5, 13-15)
#define SMALL_MAX  550

// Current joint angles — updated after every move
int currentAngles[16] = {100, 90, 90, 90, 90, 80, 90, 90, 90, 90, 100, 90, 90, 90, 95, 80};

// ============================================================
// SETUP
// ============================================================
void setup() {
  Serial.begin(115200);
  pwm.begin();
  pwm.setPWMFreq(SERVO_FREQ);

  // Drive all servos to starting positions
  for (int i = 0; i < 16; i++) { setAngle(i, currentAngles[i]); }
  goHome();

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
// broadcastAngles — streams all 16 servo positions over serial
// Called after every smoothMove so dashboard stays in sync
// ============================================================
void broadcastAngles() {
  for (int i = 0; i < 16; i++) {
    Serial.print("Servo:");
    Serial.print(i);
    Serial.print(",");
    Serial.println(currentAngles[i]);
  }
}

// ============================================================
// smoothMove — single-axis sequential motion (±1° per step)
// ============================================================
void smoothMove(int pin, int targetAngle, int speedDelay) {
  int startAngle = currentAngles[pin];
  if (startAngle == targetAngle) return;

  if (startAngle < targetAngle) {
    for (int i = startAngle; i <= targetAngle; i++) {
      setAngle(pin, i);
      delay(speedDelay);
    }
  } else {
    for (int i = startAngle; i >= targetAngle; i--) {
      setAngle(pin, i);
      delay(speedDelay);
    }
  }
  currentAngles[pin] = targetAngle;
  broadcastAngles();  // broadcast after every move
}

// ============================================================
// HANDOVER SEQUENCE
// ============================================================
void executeFullCycle() {

  // --- STEP 1: LEFT ARM PICK ---
  Serial.println("Action: Left arm picking");
  delay(1200);
  smoothMove(5, 90, 7);              // Gripper open
  smoothMove(1, 130, 17);            // Shoulder forward
  smoothMove(2, 21, 14);             // Elbow extend
  smoothMove(3, 96, 7);              // Wrist roll neutral
  smoothMove(4, 44, 7);              // Wrist pitch down
  delay(1500);
  smoothMove(5, 0, 7);               // Gripper close (grip object)
  delay(1500);

  // --- STEP 2: CENTERING ---
  Serial.println("Action: Centering mass");
  delay(1000);
  smoothMove(4, 90, 5);
  smoothMove(2, 97, 14);
  smoothMove(1, 90, 17);
  delay(2000);

  // --- STEP 3: ROTATE TO HANDOVER ---
  Serial.println("Action: Rotating to handover");
  delay(1000);
  smoothMove(0, 172, 13);            // Base rotation to face right arm
  delay(2500);

  // --- STEP 4: EXTEND TO TRANSFER POSITION ---
  Serial.println("Action: Extending left arm");
  delay(1000);
  smoothMove(1, 115, 17);
  smoothMove(2, 48, 14);
  smoothMove(4, 88, 7);
  delay(2500);

  // --- STEP 5: RIGHT ARM RECEIVE ---
  Serial.println("Action: Right arm receiving");
  delay(1200);
  smoothMove(14, 89, 7);
  smoothMove(13, 0, 7);
  smoothMove(12, 42, 14);
  smoothMove(11, 115, 17);
  smoothMove(10, 18, 13);
  delay(1800);
  smoothMove(15, 5, 7);

  Serial.println("Action: Right arm grabbing");
  delay(800);
  smoothMove(15, 0, 7);              // Right gripper closes on object
  delay(3000);

  // --- STEP 6: HANDOVER RELEASE ---
  Serial.println("Action: Left arm release");
  delay(1000);
  smoothMove(5, 90, 7);              // Left gripper opens
  delay(2000);

  // --- STEP 7: MOVE RIGHT ARM TO DROP ZONE ---
  Serial.println("Action: Right arm moving to drop zone");
  delay(1200);
  smoothMove(12, 90, 14);
  smoothMove(11, 90, 17);
  smoothMove(10, 93, 13);
  smoothMove(11, 130, 17);
  smoothMove(12, 21, 14);
  smoothMove(13, 92, 7);
  smoothMove(14, 44, 7);
  delay(2500);

  // --- STEP 8: FINAL DROP ---
  Serial.println("Action: Dropping object");
  delay(1000);
  smoothMove(15, 90, 7);             // Right gripper opens — object released
  delay(2500);

  // --- STEP 9: RETURN HOME ---
  Serial.println("Action: Homing both arms");
  delay(1000);
  homeLeft();
  delay(2500);
  homeRight();

  Serial.println("Action: Mission complete");
}

// ============================================================
// HOME POSITIONS
// ============================================================
void homeLeft() {
  smoothMove(0, 85, 13);
  smoothMove(4, 90, 7);
  smoothMove(3, 96, 7);
  smoothMove(2, 91, 15);
  smoothMove(1, 90, 17);
  smoothMove(5, 90, 7);
}

void homeRight() {
  smoothMove(14, 90, 7);
  smoothMove(13, 92, 7);
  smoothMove(12, 90, 15);
  smoothMove(11, 90, 17);
  smoothMove(10, 93, 13);
  smoothMove(15, 90, 7);
}

void goHome() {
  homeLeft();
  homeRight();
}

// ============================================================
// setAngle — drives a servo and updates currentAngles[]
// ============================================================
void setAngle(int pin, int angle) {
  int pulse = ((pin >= 0 && pin <= 2) || (pin >= 10 && pin <= 12))
              ? map(angle, 0, 180, BIG_MIN, BIG_MAX)
              : map(angle, 0, 180, SMALL_MIN, SMALL_MAX);
  pwm.setPWM(pin, 0, pulse);
}
