/*
 * Syringe Sensor Data Smoothing Using Moving Average Filter
 * This program reads quaternion data from a QTPy + BNO055 sensor and an potentiometer sensor (for plunger),
 * applies a moving average filter, using a circular buffer to both, and prints the smoothed values to the serial monitor.
 * 
 * Author: Pi Ko (pk2269@nyu.edu)
 * Date: 10 June 2024
 */

#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

/* Set the delay between fresh samples */
uint16_t BNO055_SAMPLERATE_DELAY_MS = 10;

Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28, &Wire);

// Define the size of the moving average window
const int windowSize = 10;
imu::Quaternion quatBuffer[windowSize];
float sensorValueBuffer[windowSize];
int bufferIndex = 0;

/**
 * Sets up the sensor and serial communication.
 */
void setup(void) {
  Serial.begin(115200);
  while (!Serial) {
    delay(10);
  }

  Serial.println("Orientation Sensor Test");
  Serial.println("");

  if (!bno.begin()) {
    Serial.print("Ooops, no BNO055 detected ... Check your wiring or I2C ADDR!");
    while (1);
  }

  bno.setMode(OPERATION_MODE_NDOF);
  delay(1000);

  // Initialize buffers with default values
  for (int i = 0; i < windowSize; i++) {
    quatBuffer[i] = imu::Quaternion(1, 0, 0, 0);  // Identity quaternion
    sensorValueBuffer[i] = 0.0;
  }
}

/**
 * Main loop: Reads data, applies moving average filter, and prints results.
 */
void loop(void) {
  // Read raw data
  imu::Quaternion rawQuat = bno.getQuat();
  float rawSensorValue = analogRead(A0);
  rawSensorValue = rawSensorValue / 4095 * -1 + 1;

  // Update buffers
  quatBuffer[bufferIndex] = rawQuat;
  sensorValueBuffer[bufferIndex] = rawSensorValue;
  bufferIndex = (bufferIndex + 1) % windowSize;

  // Compute averages
  imu::Quaternion avgQuat = averageQuat();
  float avgSensorValue = averageSensor();

  // Print averaged data
  printQuaternion(avgQuat, avgSensorValue);

  delay(BNO055_SAMPLERATE_DELAY_MS);
}

/**
 * Prints quaternion and sensor values to the serial monitor.
 * @param quat The quaternion to print.
 * @param sensorValue The sensor value to print.
 */
void printQuaternion(const imu::Quaternion& quat, float sensorValue) {
  Serial.print("Quat W:");
  Serial.print(quat.w(), 4);
  Serial.print(", X:");
  Serial.print(quat.x(), 4);
  Serial.print(", Y:");
  Serial.print(quat.y(), 4);
  Serial.print(", Z:");
  Serial.print(quat.z(), 4);
  Serial.print(",");
  Serial.println(sensorValue);
}

/**
 * Averages the stored quaternions.
 * @return The average quaternion.
 */
imu::Quaternion averageQuat() {
  float sumW = 0, sumX = 0, sumY = 0, sumZ = 0;
  for (int i = 0; i < windowSize; i++) {
    sumW += quatBuffer[i].w();
    sumX += quatBuffer[i].x();
    sumY += quatBuffer[i].y();
    sumZ += quatBuffer[i].z();
  }
  return imu::Quaternion(sumW / windowSize, sumX / windowSize, sumY / windowSize, sumZ / windowSize);
}

/**
 * Averages the stored sensor values.
 * @return The average sensor value.
 */
float averageSensor() {
  float sum = 0;
  for (int i = 0; i < windowSize; i++) {
    sum += sensorValueBuffer[i];
  }
  return sum / windowSize;
}
