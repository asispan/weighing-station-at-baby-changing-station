# DIY Baby Weighing Scale at Diaper Changing Station

A guide for building a professional baby weighing station using load cells, HX711 amplifiers, Raspberry Pi Zero 2W, and LCD display.

## Table of Contents
- [Project Overview](#project-overview)
- [Key Specifications](#key-specifications)  
- [Required Components](#required-components)
- [Hardware Architecture](#hardware-architecture)
- [Pin Mapping](#pin-mapping)
- [Software Installation](#software-installation)
- [Python Code Files](#python-code-files)
- [Calibration Process](#calibration-process)
- [Mechanical Assembly](#mechanical-assembly)
- [Operating Principle](#operating-principle)
- [Webhook Integration](#webhook-integration)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Safety and Maintenance](#safety-and-maintenance)
- [License](#license)

## Project Overview

This DIY weighing station provides an accurate, affordable solution for monitoring baby weight at changing stations. The system uses four precision load cells positioned at the corners of a glass platform, with readings processed by a Raspberry Pi Zero 2W and displayed on an LCD screen. The platform weight is automatically tared in software, ensuring only the baby's weight is measured.

## Key Specifications

- **Maximum Capacity**: 20 kg (4 x 5 kg load cells)
- **Platform Size**: 48 cm x 80 cm glass top
- **Display**: LCD1602 with I2C interface  
- **Controller**: Raspberry Pi Zero 2W
- **Update Rate**: Approximately 0.5 seconds
- **ADC Resolution**: 24-bit via HX711 modules
- **Power Requirements**: 5V 2.5A recommended
- **Accuracy**: +/- 10 grams after calibration

## Required Components

### Electronics
- 1x Raspberry Pi Zero 2W with headers
- 4x 5kg load cells (strain gauge type)
- 4x HX711 amplifier modules
- 1x LCD1602 I2C display module
- 1x Breadboard for connections
- Jumper wires (male-to-female and male-to-male)
- 5V 2.5A power supply with micro USB cable

### Mechanical
- 48 cm x 80 cm tempered glass plate (8-10mm thick)
- Load cell mounting brackets or 3D printed mounts
- M4 or M5 bolts and nuts for mounting
- Cable management clips
- Protective enclosure for electronics (optional)

## Hardware Architecture

### Component Connections

The system employs a distributed architecture where each load cell connects to its dedicated HX711 amplifier. All four HX711 modules share power rails but use separate GPIO data lines to enable simultaneous readings.

**Load Cell to HX711 Wiring**:
- Red wire connects to E+ (Excitation positive)
- Black wire connects to E- (Excitation negative)  
- Green wire connects to A+ (Signal positive)
- White wire connects to A- (Signal negative)

Note: Wire colors may vary by manufacturer. Always verify with multimeter if uncertain.

## Pin Mapping

### HX711 Modules to Raspberry Pi

| Module Position | Data Pin (DT) | Clock Pin (SCK) | Power (VCC) | Ground (GND) |
|-----------------|---------------|-----------------|-------------|--------------|
| Front-Left      | GPIO 5 (Pin 29) | GPIO 6 (Pin 31) | 3.3V (Pin 17) | GND (Pin 39) |
| Front-Right     | GPIO 13 (Pin 33) | GPIO 19 (Pin 35) | 3.3V (Pin 17) | GND (Pin 39) |
| Back-Left       | GPIO 26 (Pin 37) | GPIO 16 (Pin 36) | 3.3V (Pin 17) | GND (Pin 39) |
| Back-Right      | GPIO 20 (Pin 38) | GPIO 21 (Pin 40) | 3.3V (Pin 17) | GND (Pin 39) |

### LCD1602 I2C Display to Raspberry Pi

| LCD Pin | Raspberry Pi Pin | GPIO Number |
|---------|------------------|-------------|
| VCC     | Pin 1            | 3.3V        |
| GND     | Pin 9            | Ground      |
| SDA     | Pin 3            | GPIO 2      |
| SCL     | Pin 5            | GPIO 3      |

## Software Installation

### Step 1: System Preparation

Update your Raspberry Pi OS and enable I2C interface:

```bash
sudo apt-get update
sudo apt-get upgrade -y
sudo raspi-config
```

Navigate to: Interface Options -> I2C -> Yes -> Finish -> Reboot

### Step 2: Install Required Packages

Install system packages and Python libraries:

```bash
sudo apt-get install -y i2c-tools python3-smbus python3-pip git
pip3 install RPi.GPIO smbus2 requests
```

### Step 3: Install HX711 Library

```bash
pip3 install hx711-rpi-py
```

### Step 4: Verify I2C Connection

Check if LCD is detected (should show address 0x27 or 0x3F):

```bash
sudo i2cdetect -y 1
```

### Step 5: Clone Project Repository

```bash
git clone https://github.com/asispan/weighing-station-at-baby-changing-station.git
cd weighing-station-at-baby-changing-station
```

## Python Code Files

### calibration.py
Interactive calibration wizard that guides through:
- Zero/tare calibration with no load
- Scale calibration with known weights
- Automatic calculation of offset and scale factors
- Saves calibration values to file

### weighing_machine.py
Main application that:
- Reads from all four load cells
- Applies calibration corrections
- Displays real-time weight on LCD
- Handles automatic taring
- Provides console output for debugging

### weighing_machine_webhook.py
Extended version with IoT capabilities:
- All features of weighing_machine.py
- Sends weight data to webhook endpoints
- JSON payload formatting
- Configurable transmission intervals
- Error handling for network issues

## Calibration Process

Accurate calibration is crucial for reliable measurements. The process involves two stages:

### Stage 1: Zero Calibration (Tare)

1. Ensure the platform is completely empty
2. Run the calibration script:
   ```bash
   python3 calibration.py
   ```
3. Follow prompts to begin zero calibration
4. Script takes 10 readings from each sensor
5. Calculates and stores offset values

### Stage 2: Scale Calibration

1. Place a known weight (e.g., 1000g) on each corner when prompted
2. Enter the exact weight value in grams
3. Script calculates scale factors using formula:
   ```
   scale_factor = (reading - offset) / known_weight
   ```
4. Calibration values are saved to `calibration_values.txt`

### Stage 3: Apply Calibration

Copy the generated values into the CALIBRATION array in weighing_machine.py:

```python
CALIBRATION = [
    {'offset': 8430.0, 'scale': 215.3},  # Front-Left
    {'offset': 8350.0, 'scale': 214.7},  # Front-Right
    {'offset': 8510.0, 'scale': 216.1},  # Back-Left
    {'offset': 8420.0, 'scale': 215.0}   # Back-Right
]
```

## Mechanical Assembly

### Load Cell Mounting

1. Position each load cell 5-10 cm from platform corners
2. Ensure arrow on load cell points downward
3. Use standoffs to allow proper flexing
4. Maintain adequate clearance for deformation
5. Secure with appropriate bolts (M4 or M5)

### Platform Installation

1. Place glass platform on load cell mounting points
2. Ensure platform sits level and stable
3. Add rubber pads if needed for grip
4. Verify no binding or interference

### Cable Management

1. Route wires away from moving parts
2. Use cable clips to secure wiring
3. Keep data lines away from power cables
4. Use breadboard for organized connections
5. Consider shielded cables in noisy environments

## Operating Principle

The weighing system operates through the following sequence:

1. **Force Application**: Weight on platform creates mechanical stress on load cells
2. **Strain Measurement**: Internal strain gauges change resistance proportionally
3. **Signal Amplification**: HX711 modules amplify millivolt signals to readable levels
4. **Digital Conversion**: 24-bit ADC converts analog signals to digital values
5. **Data Acquisition**: Raspberry Pi reads digital values via GPIO
6. **Calibration Application**: Software applies offset and scale corrections
7. **Weight Calculation**: Individual readings are summed for total weight
8. **Display Update**: LCD shows current weight in grams or kilograms
9. **Optional Transmission**: Webhook sends data to cloud endpoints

## Webhook Integration

The webhook-enabled version supports IoT integration for remote monitoring and data logging.

### Configuration

Edit these parameters in `weighing_machine_webhook.py`:

```python
WEBHOOK_ENABLED = True
WEBHOOK_URL = "https://your-server.com/api/weight"
DEVICE_ID = "baby_scale_001"
SEND_INTERVAL = 5  # seconds
```

### JSON Payload Format

```json
{
  "timestamp": "2025-10-23T19:30:45",
  "device_id": "baby_scale_001",
  "total_weight_grams": 7535.2,
  "total_weight_kg": 7.535,
  "sensors": [
    {"sensor": "sensor_1", "weight_grams": 1883.8},
    {"sensor": "sensor_2", "weight_grams": 1884.1},
    {"sensor": "sensor_3", "weight_grams": 1883.5},
    {"sensor": "sensor_4", "weight_grams": 1883.8}
  ]
}
```

### Use Cases

- Real-time monitoring dashboards
- Historical weight tracking
- Growth chart generation
- Alert systems for weight changes
- Integration with health record systems

## Troubleshooting Guide

### LCD Display Issues

**Problem**: LCD shows nothing or garbage characters
- Verify I2C is enabled in raspi-config
- Check I2C address matches code (0x27 or 0x3F)
- Ensure proper SDA/SCL connections
- Verify 3.3V power to LCD module
- Try adjusting contrast potentiometer on LCD backpack

### Sensor Reading Issues

**Problem**: No readings or constant zero values
- Check GPIO pin assignments match code
- Verify HX711 module power (LED indicator)
- Test continuity of all connections
- Ensure load cells are properly connected
- Try reading single sensor in isolation

**Problem**: Negative weight values
- Swap A+ and A- wires on affected sensor
- Or invert scale factor in calibration
- Recalibrate with proper zero reference

**Problem**: Unstable or drifting readings
- Check for loose connections
- Shield from electromagnetic interference  
- Ensure stable power supply
- Allow warm-up time (5 minutes)
- Recalibrate if drift persists

### Communication Issues

**Problem**: Webhook fails to send
- Verify network connectivity
- Check webhook URL is accessible
- Review firewall settings
- Examine response codes in console
- Increase timeout values if needed

## Safety and Maintenance

### Safety Guidelines

- Never exceed 20 kg total weight capacity
- Keep electronics away from liquids
- Use proper electrical insulation
- Ensure stable platform mounting
- Supervise children during use
- Disconnect power when not in use

### Routine Maintenance

**Daily**:
- Wipe platform with appropriate cleaner
- Check for visible damage or wear

**Weekly**:
- Verify all connections are secure
- Clean sensor mounting areas
- Test with known weight for accuracy

**Monthly**:
- Recalibrate if readings drift
- Inspect cables for damage
- Clean electronic components with compressed air
- Update software if new versions available

**Quarterly**:
- Full system recalibration
- Check mounting hardware torque
- Review and clean webhook logs
- Backup calibration values

### Calibration Schedule

Recalibrate when:
- Initial setup is complete
- Sensors or hardware are replaced
- Readings drift more than 50g
- Platform or mounting is adjusted
- After transportation or impact

## License

This project is open source and available under the MIT License. Feel free to modify, distribute, and use in commercial applications with attribution.

---

**Project Repository**: [https://github.com/asispan/weighing-station-at-baby-changing-station](https://github.com/asispan/weighing-station-at-baby-changing-station)

**Contributors Welcome**: Submit issues, pull requests, or feature suggestions via GitHub.

**Support**: For questions or support, please open an issue on the GitHub repository.
