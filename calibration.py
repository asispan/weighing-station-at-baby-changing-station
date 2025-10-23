#!/usr/bin/env python3
"""
calibration.py - Load Cell Calibration Script
This script calibrates four HX711 load cell amplifiers connected to a Raspberry Pi Zero 2W.
Calibration is performed in two stages:
1. Zero calibration (tare) - establishes baseline with no weight
2. Scale calibration - calculates conversion factors using known weights
"""

import time
import RPi.GPIO as GPIO
from hx711 import HX711

# GPIO Pin Configuration for Four HX711 Modules
HX711_CONFIGS = [
    {'name': 'Front-Left',  'dout': 5,  'pd_sck': 6},   # HX711_1
    {'name': 'Front-Right', 'dout': 13, 'pd_sck': 19},  # HX711_2
    {'name': 'Back-Left',   'dout': 26, 'pd_sck': 16},  # HX711_3
    {'name': 'Back-Right',  'dout': 20, 'pd_sck': 21}   # HX711_4
]

# Number of samples for averaging
SAMPLES = 10

def cleanup():
    """Clean up GPIO on exit"""
    GPIO.cleanup()

def initialize_sensors():
    """Initialize all four HX711 sensors"""
    sensors = []
    for config in HX711_CONFIGS:
        hx = HX711(dout_pin=config['dout'], pd_sck_pin=config['pd_sck'])
        hx.reset()
        sensors.append({
            'name': config['name'],
            'hx': hx,
            'offset': 0,
            'scale': 1
        })
    return sensors

def calibrate_zero(sensors):
    """Stage 1: Zero calibration (tare) - record baseline readings"""
    print("\n" + "="*60)
    print("STAGE 1: ZERO CALIBRATION (TARE)")
    print("="*60)
    print("\nPlease ensure NO WEIGHT is on the scale.")
    input("Press Enter when ready to begin zero calibration...")

    print(f"\nTaking {SAMPLES} readings from each sensor...")

    for sensor in sensors:
        readings = []
        print(f"\nCalibrating {sensor['name']}...")

        for i in range(SAMPLES):
            reading = sensor['hx'].get_raw_data_mean()
            if reading:
                readings.append(reading)
                print(f"  Reading {i+1}/{SAMPLES}: {reading}")
            time.sleep(0.1)

        if readings:
            sensor['offset'] = sum(readings) / len(readings)
            print(f"  âœ“ Average offset: {sensor['offset']:.2f}")
        else:
            print(f"  âœ— ERROR: No valid readings from {sensor['name']}")

    return sensors

def calibrate_scale(sensors, known_weight_grams):
    """Stage 2: Scale calibration - calculate conversion factors"""
    print("\n" + "="*60)
    print("STAGE 2: SCALE FACTOR CALIBRATION")
    print("="*60)
    print(f"\nPlace a known weight of {known_weight_grams}g on EACH corner.")
    input("Press Enter when ready to begin scale calibration...")

    print(f"\nTaking {SAMPLES} readings from each sensor...")

    for sensor in sensors:
        readings = []
        print(f"\nCalibrating {sensor['name']}...")

        for i in range(SAMPLES):
            reading = sensor['hx'].get_raw_data_mean()
            if reading:
                readings.append(reading)
                print(f"  Reading {i+1}/{SAMPLES}: {reading}")
            time.sleep(0.1)

        if readings:
            avg_reading = sum(readings) / len(readings)
            # Calculate scale factor: (reading - offset) / known_weight
            sensor['scale'] = (avg_reading - sensor['offset']) / known_weight_grams
            print(f"  âœ“ Average reading: {avg_reading:.2f}")
            print(f"  âœ“ Scale factor: {sensor['scale']:.6f}")
        else:
            print(f"  âœ— ERROR: No valid readings from {sensor['name']}")

    return sensors

def save_calibration(sensors, filename='calibration_values.txt'):
    """Save calibration values to file"""
    print("\n" + "="*60)
    print("SAVING CALIBRATION VALUES")
    print("="*60)

    with open(filename, 'w') as f:
        f.write("# Calibration values for weighing machine\n")
        f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        for i, sensor in enumerate(sensors):
            f.write(f"# {sensor['name']}\n")
            f.write(f"OFFSET_{i+1} = {sensor['offset']:.2f}\n")
            f.write(f"SCALE_{i+1} = {sensor['scale']:.6f}\n\n")

    print(f"\nâœ“ Calibration values saved to '{filename}'")
    print("\nCopy these values to your weighing_machine.py:")
    print("\nCALIBRATION = [")
    for sensor in sensors:
        print(f"    {{'offset': {sensor['offset']:.2f}, 'scale': {sensor['scale']:.6f}}},  # {sensor['name']}")
    print("]\n")

def main():
    """Main calibration routine"""
    try:
        print("\n" + "="*60)
        print("LOAD CELL CALIBRATION WIZARD")
        print("="*60)
        print("This script will calibrate four HX711 load cell amplifiers.")

        # Initialize sensors
        print("\nInitializing sensors...")
        sensors = initialize_sensors()
        print("âœ“ All sensors initialized")

        # Stage 1: Zero calibration
        sensors = calibrate_zero(sensors)

        # Stage 2: Scale calibration
        print("\nEnter the known weight in grams (e.g., 1000 for 1kg):")
        known_weight = float(input("Known weight (grams): "))
        sensors = calibrate_scale(sensors, known_weight)

        # Save calibration values
        save_calibration(sensors)

        print("\n" + "="*60)
        print("CALIBRATION COMPLETE!")
        print("="*60)
        print("\nNext steps:")
        print("1. Update CALIBRATION array in weighing_machine.py")
        print("2. Run weighing_machine.py to test the scale")
        print("\n")

    except KeyboardInterrupt:
        print("\n\nCalibration interrupted by user.")
    except Exception as e:
        print(f"\n\nERROR: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    main()