#include <IRremote.hpp>
#include <LiquidCrystal.h>

// === Pin Setup ===
#define IR_RECEIVE_PIN 8
#define RED_PIN 9
#define GREEN_PIN 10
#define BLUE_PIN 11

LiquidCrystal lcd(7, 12, 5, 4, 3, 2);

int currentPlanet = 0;  // 0 = Earth, 1 = Moon, 2 = Mars

// Planet color definitions
struct PlanetColor {
  int r, g, b;
  String name;
};

PlanetColor planets[3] = {
  {230, 255, 0, "Earth"},      // Yellowish orange
  {100, 150, 255, "Moon"},     // White
  {0, 0, 255, "Mars"}          // Blue
};

// Sunrise variables
bool sunriseActive = false;
unsigned long sunriseStartTime = 0;
int targetR = 0, targetG = 0, targetB = 0;
unsigned long sunriseDuration = 0;

void setup() {
  Serial.begin(9600);
  
  // Initialize IR receiver
  IrReceiver.begin(IR_RECEIVE_PIN, ENABLE_LED_FEEDBACK);
  
  // Initialize LCD
  lcd.begin(16, 2);
  lcd.clear();
  lcd.print("Ready!");
  
  // Initialize RGB LED pins
  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
  
  // Turn off LED initially
  setColor(0, 0, 0);
  
  Serial.println("System Ready");
  Serial.println("Use UP/DOWN arrows");
  
  delay(1000);
  showPlanet(0);  // Start with Earth
}

void loop() {
  // Check for serial commands from Python
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command.startsWith("SUNRISE")) {
      parseAndStartSunrise(command);
    }
  }
  
  // Handle sunrise animation
  if (sunriseActive) {
    updateSunrise();
  }
  
  // Handle IR remote (only if sunrise is not active)
  if (!sunriseActive && IrReceiver.decode()) {
    unsigned long command = IrReceiver.decodedIRData.command;
    
    Serial.print("Button: ");
    Serial.println(command);
    
    // Handle button presses
    if (command == 9) {  // UP arrow
      currentPlanet++;
      if (currentPlanet > 2) currentPlanet = 0;  // Wrap around
      showPlanet(currentPlanet);
      Serial.print("-> Planet: ");
      Serial.println(currentPlanet);
    } 
    else if (command == 7) {  // DOWN arrow
      currentPlanet--;
      if (currentPlanet < 0) currentPlanet = 2;  // Wrap around
      showPlanet(currentPlanet);
      Serial.print("-> Planet: ");
      Serial.println(currentPlanet);
    }
    
    IrReceiver.resume();
  }
}

void parseAndStartSunrise(String command) {
  // Expected format: "SUNRISE DURATION"
  // Example: "SUNRISE 30000"
  // Now uses current planet's colors instead of passed RGB values
  
  int firstSpace = command.indexOf(' ');
  
  if (firstSpace > 0) {
    sunriseDuration = command.substring(firstSpace + 1).toInt();
    
    // Use current planet's colors as target
    targetR = planets[currentPlanet].r;
    targetG = planets[currentPlanet].g;
    targetB = planets[currentPlanet].b;
    
    // Start sunrise
    sunriseActive = true;
    sunriseStartTime = millis();
    setColor(0, 0, 0);  // Start from off
    
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Sunrise: ");
    lcd.print(planets[currentPlanet].name);
    lcd.setCursor(0, 1);
    lcd.print("Waking up...");
    
    Serial.print("✅ Sunrise started on ");
    Serial.println(planets[currentPlanet].name);
    Serial.print("Target RGB: ");
    Serial.print(targetR);
    Serial.print(", ");
    Serial.print(targetG);
    Serial.print(", ");
    Serial.println(targetB);
    Serial.print("Duration: ");
    Serial.print(sunriseDuration);
    Serial.println(" ms");
  } else {
    Serial.println("❌ Invalid SUNRISE command format");
  }
}

void updateSunrise() {
  unsigned long elapsedTime = millis() - sunriseStartTime;
  
  if (elapsedTime >= sunriseDuration) {
    // Sunrise complete
    sunriseActive = false;
    setColor(targetR, targetG, targetB);
    
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Good Morning!");
    lcd.setCursor(0, 1);
    lcd.print(planets[currentPlanet].name);
    
    Serial.println("🌅 Sunrise complete!");
  } else {
    // Calculate current brightness (linear interpolation)
    float progress = (float)elapsedTime / (float)sunriseDuration;
    
    int currentR = (int)(targetR * progress);
    int currentG = (int)(targetG * progress);
    int currentB = (int)(targetB * progress);
    
    setColor(currentR, currentG, currentB);
  }
}

void showPlanet(int planet) {
  // Stop sunrise if active
  sunriseActive = false;
  
  switch(planet) {
    case 0:  // Earth
      displayPlanet("Earth: Home", planets[0].r, planets[0].g, planets[0].b);
      break;
    case 1:  // Moon
      displayPlanet("Moon: Earth's", "Lil sis", planets[1].r, planets[1].g, planets[1].b);
      break;
    case 2:  // Mars
      displayPlanet("Mars: Earth's", "Lil bro", planets[2].r, planets[2].g, planets[2].b);
      break;
  }
}

// Function to display text on LCD and set RGB color
void displayPlanet(String line1, int r, int g, int b) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1);
  setColor(r, g, b);
}

// Overloaded function for two-line display
void displayPlanet(String line1, String line2, int r, int g, int b) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1);
  lcd.setCursor(0, 1);
  lcd.print(line2);
  setColor(r, g, b);
}

// Function to set RGB LED color - NO INVERSION (common cathode)
void setColor(int red, int green, int blue) {
  analogWrite(RED_PIN, red);
  analogWrite(GREEN_PIN, green);
  analogWrite(BLUE_PIN, blue);
}