void setup() {
  Serial.begin(115200);
}

// Define the number of samples for the moving average
const int numSamples = 10;
int readings[numSamples]; // Array to store the readings
int readIndex = 0; // the index of the current reading
float total = 0; // the running total
float average = 0; // the average

void loop() {
  // Read the value from analog pin A7
  float val = analogRead(A7);
  
  // Subtract the oldest reading from the total
  total = total - readings[readIndex];
  
  // Read from the sensor and map the value to 0-100
  readings[readIndex] = constrain(map(val, 250, 100, 0, 100), 0, 100);
  
  // Add the latest reading to the total
  total = total + readings[readIndex];
  
  // Advance to the next position in the array
  readIndex = readIndex + 1;
  
  // If we're at the end of the array, wrap around to the beginning
  if (readIndex >= numSamples) {
    readIndex = 0;
  }
  
  // Calculate the average
  average = total / numSamples;
  
  // Print the average value
  Serial.print("Cheek : ");
  Serial.println(average);
  
  // Delay of 100 milliseconds before the next loop
  delay(100);
}
