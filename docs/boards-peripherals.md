# Tested Boards and Peripherals

## Tested Boards
We consider three platform-framework combinations, where each platform refers to a specific MCU development board paired with its corresponding embedded framework:

- ATmega2560 (Arduino Mega 2560 Rev3) with the Arduino framework (Arduino CLI v1.4.1, Arduino Core arduino:avr v1.8.7);
- ESP32-S3 (ESP32-S3-BOX-3) with ESP-IDF (v5.1.2);
- nRF52840 (Arduino Nano 33 BLE Rev2) with Zephyr via nRF Connect SDK (v2.7.0);
- TI MSP430 (msp430fr5994) LaunchPad with MSP430-GCC Makefile ramework.

## Tested Peripherals

Table: List of peripherals Tested by IoT-SkillsBench.

| # | Peripheral | Interface | Category |
| :--- | :--- | :--- | :--- |
| 1 | LED | GPIO (Digital Out) | Actuator |
| 2 | Push Button | GPIO (Digital In) | Input |
| 3 | Active Buzzer | GPIO (Digital Out) | Actuator |
| 4 | Passive Buzzer | PWM | Actuator |
| 5 | Relay Module | GPIO (Digital Out) | Actuator |
| 6 | Laser Emitter Module | GPIO (Digital Out) | Actuator |
| 7 | Rotary Encoder | GPIO (Digital In) | Input |
| 8 | 16-Key Keypad (4×4) | GPIO (Digital In) | Input |
| 9 | Tilt Switch (KY-020) | GPIO (Digital In) | Input |
| 10 | Analog Joystick | ADC | Input |
| 11 | Photoresistor (KY-018) | ADC | Sensor |
| 12 | TMP36 Temperature Sensor | ADC | Sensor |
| 13 | Analog Water Level Sensor | ADC | Sensor |
| 14 | PIR Motion Sensor (HC-SR501) | GPIO (Digital In) | Sensor |
| 15 | Ultrasonic Sensor (HC-SR04) | GPIO (Trigger/Echo) | Sensor |
| 16 | Digital Sound Sensor | GPIO (Digital In) | Sensor |
| 17 | Digital Shock Sensor | GPIO (Digital In) | Sensor |
| 18 | DHT11 (Temp & Humidity) | 1-Wire | Sensor |
| 19 | DS18B20 (Temperature) | 1-Wire | Sensor |
| 20 | LCD1602 Display (HD44780) | GPIO (Parallel) | Output |
| 21 | DS1307 RTC Module | I2C | Sensor |
| 22 | MPU6050 / GY-521 | I2C | Sensor |
| 23 | BME280 (Temp, Humidity, Pres.) | I2C / SPI | Sensor |
| 24 | Onboard LED | GPIO Digital Out | Actuator |
| 25 | Optional LCD control pin | GPIO Digital Out | Output control |
| # | Peripheral | Interface | Category |
|---|---|---|---|

