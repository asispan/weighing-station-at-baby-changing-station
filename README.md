# Baby Weighing Station at Changing Station

A DIY solution for accurately weighing babies at changing stations using a Raspberry Pi Zero 2W, four load cells, HX711 amplifiers, and an LCD1602 I2C Display. This guide covers the project architecture, hardware setup, software installation, calibration method, and future-proof IoT extensions.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Key Specifications](#key-specifications)
- [Hardware Architecture](#hardware-architecture)
  - [Component Connections](#component-connections)
  - [Pin Mapping](#pin-mapping)
- [Software Installation](#software-installation)
- [Calibration Process](#calibration-process)
- [Mechanical Assembly](#mechanical-assembly)
- [Operating Principle](#operating-principle)
- [Webhook Integration (Future Scope)](#webhook-integration-future-scope)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Safety and Maintenance](#safety-and-maintenance)
- [Project Files](#project-files)

---

## Project Overview

The Baby Weighing Station is an affordable, robust weighing platform purpose-built for baby changing stations. It employs four 5kg load cells, each amplified by a dedicated HX711 module. Readings are processed by a Raspberry Pi Zero 2W and displayed on an LCD1602 I2C screen. This system enables rapid, hands-free, and precise weight checks directly at the changing station.

## Key Specifications
- **Maximum Capacity**: 20kg (4 Ã— 5kg load cells)
- **Platform Size**: 48cm Ã— 80cm glass top
- **Display**: LCD1602 I2C interface
- **Controller**: Raspberry Pi Zero 2W
- **Update Rate**: ~0.5 seconds
- **ADC Resolution**: 24-bit via HX711 modules

## Hardware Architecture
### Component Connections
Each load cell connects to its own HX711 amplifier. All four HX711 modules share power and clock signals, while their data output lines connect to separate Raspberry Pi GPIO pins:
- Red (E+) â†’ HX711 E+
- Black (E-) â†’ HX711 E-
- Green (A+) â†’ HX711 A+
- White (A-) â†’ HX711 A-

### Pin Mapping
| Module                | DT Pin          | SCK Pin         | VCC          | GND         |
|-----------------------|-----------------|-----------------|--------------|-------------|
| HX711_1 (Front-Left)  | GPIO 5 (Pin 29) | GPIO 6 (Pin 31) | 3.3V (Pin 17)| GND (39)    |
| HX711_2 (Front-Right) | GPIO 13 (Pin 33)| GPIO 19 (Pin 35)| ""           | ""          |
| HX711_3 (Back-Left)   | GPIO 26 (Pin 37)| GPIO 16 (Pin 36)| ""           | ""          |
| HX711_4 (Back-Right)  | GPIO 20 (Pin 38)| GPIO 21 (Pin 40)| ""           | ""          |

LCD1602 I2C:
- VCC â†’ Pin 1 (3.3V)
- GND â†’ Pin 9
- SDA â†’ Pin 3 (GPIO 2)
- SCL â†’ Pin 5 (GPIO 3)

All HX711 modules share power rails using a breadboard.

## Software Installation
1. **Update RPi Zero 2W & Enable I2C**:
    ```bash
    sudo apt-get update && sudo apt-get upgrade -y
    sudo raspi-config   # Interface Options â†’ I2C â†’ Yes â†’ Reboot
    ```
2. **Install Packages & Python Libraries**:
    ```bash
    sudo apt-get install -y i2c-tools python3-smbus python3-pip
    pip3 install RPi.GPIO smbus2 requests hx711-rpi-py
    ```
3. **Verify I2C LCD Connection**:
    ```bash
    sudo i2cdetect -y 1
    ```

## Calibration Process
- **Zero Calibration (Tare)**: Remove all weights, run `python3 calibration.py`, 10 averages per sensor; establishes sensor offset.
- **Scale Calibration**: Place a known weight on each corner, record readings, calculate scale factor `(reading - offset) / known_weight` for each sensor; results stored in `calibration_values.txt`.
- **Apply Calibration**: Copy output values to `CALIBRATION` array in `weighing_machine.py`.

## Mechanical Assembly
- **Load Cell Placement**: Anchor each sensor 5-10cm from platform edge with arrow downward; use standoffs for flex; ensure secure mounting and clearance for deformation.
- **Wiring Management**: Use breadboard for power distribution; keep wiring neat to avoid interference and shorts.

## Operating Principle
- **Sensor Reading**: Mechanical force deforms load cells, changes resistance.
- **Signal Amplification**: HX711 amplifies and digitizes.
- **Communication**: Each HX711 â†’ Pi via DT pin, shared SCK.
- **Calibration Correction**: Pi applies calibration math to each sensor.
- **Display**: LCD shows total weight.

## Webhook Integration (Future Scope)
- Configure `weighing_machine_webhook.py` for IoT/remote monitoring.
- Sends JSON payloads to user-server with device data and timestamp.
- Cloud dashboard and automated logging possible with this extension.

Example payload:
```json
{
  "timestamp": "2025-10-21T20:39:00",
  "total_weight_grams": 1523.4,
  "total_weight_kg": 1.523,
  "sensors": [
    {"sensor": "sensor_1", "weight_grams": 381.2},
    {"sensor": "sensor_2", "weight_grams": 379.8},
    {"sensor": "sensor_3", "weight_grams": 382.7},
    {"sensor": "sensor_4", "weight_grams": 379.7}
  ],
  "device_id": "pi_zero_scale_001"
}
```

## Troubleshooting Guide
- **LCD Not Displaying**: Verify I2C connections/address (try 0x3F if 0x27 fails), ensure power and SDA/SCL wiring.
- **No Sensor Readings**: Check GPIO assignments, HX711 wiring, verify with multimeter.
- **Negative Weight**: Swap A+/A- wiring or invert scale factor.
- **Unstable Values**: Inspect connections, shield from interference, recalibrate.
- **Single Sensor Issues**: Check mount and wiring; recalibrate individually.

## Safety and Maintenance
- Never exceed 20kg capacity.
- Keep electronics dry and protected.
- Use proper power supply (5V, 2.5A recommended).
- Inspect wires, clean sensors/platform regularly.
- Recalibrate as readings drift (every few months).
- Update routine maintenance and firmware often.

## Project Files
- **calibration.py**: Sensor calibration wizard.
- **weighing_machine.py**: Main weighing logic.
- **weighing_machine_webhook.py**: Advanced IoT/webhook extension.
- **INSTALLATION_GUIDE.md**: Step-by-step hardware and software setup.
- **PROJECT_SUMMARY.md**: In-depth technical documentation.
- **QUICK_REFERENCE.txt**: Wiring/config cheat sheet.
- **pin_mapping.csv**: Pin assignment table.
- **Wiring diagrams**: Visual connection guides.

---

**Professional documentation, detailed code, and project assets ensure quick deployment and easy maintenance for the Baby Weight Station. For code details, see `calibration.py`, `weighing_machine.py`, and `weighing_machine_webhook.py` within this repo.**
