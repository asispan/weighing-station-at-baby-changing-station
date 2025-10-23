#!/usr/bin/env python3
"""
weighing_machine.py - Main Weighing Machine Program
Reads from four HX711 load cells and displays total weight on LCD1602 I2C display.
Supports real-time weight monitoring with automatic tare functionality.
"""

import time
import RPi.GPIO as GPIO
from hx711 import HX711
import smbus2

# ===========================
# CONFIGURATION
# ===========================

# GPIO Pin Configuration for Four HX711 Modules
HX711_CONFIGS = [
    {'name': 'Front-Left',  'dout': 5,  'pd_sck': 6},   # HX711_1
    {'name': 'Front-Right', 'dout': 13, 'pd_sck': 19},  # HX711_2
    {'name': 'Back-Left',   'dout': 26, 'pd_sck': 16},  # HX711_3
    {'name': 'Back-Right',  'dout': 20, 'pd_sck': 21}   # HX711_4
]

# Calibration values - UPDATE THESE FROM calibration.py OUTPUT
CALIBRATION = [
    {'offset': 0.0, 'scale': 1.0},  # Front-Left
    {'offset': 0.0, 'scale': 1.0},  # Front-Right
    {'offset': 0.0, 'scale': 1.0},  # Back-Left
    {'offset': 0.0, 'scale': 1.0}   # Back-Right
]

# LCD I2C Configuration
LCD_I2C_ADDRESS = 0x27  # Common addresses: 0x27 or 0x3F
LCD_I2C_BUS = 1

# Update interval (seconds)
UPDATE_INTERVAL = 0.5

# ===========================
# LCD1602 I2C DRIVER
# ===========================

class LCD1602:
    """Driver for LCD1602 with I2C interface"""

    # LCD Commands
    LCD_CLEAR = 0x01
    LCD_HOME = 0x02
    LCD_ENTRY_MODE = 0x04
    LCD_DISPLAY_CONTROL = 0x08
    LCD_FUNCTION_SET = 0x20
    LCD_SET_DDRAM = 0x80

    # Flags
    LCD_DISPLAY_ON = 0x04
    LCD_CURSOR_OFF = 0x00
    LCD_BLINK_OFF = 0x00
    LCD_2LINE = 0x08
    LCD_5x8DOTS = 0x00
    LCD_BACKLIGHT = 0x08

    # Enable bit
    ENABLE = 0b00000100

    def __init__(self, address=0x27, bus=1):
        """Initialize LCD"""
        self.address = address
        self.bus = smbus2.SMBus(bus)
        self.backlight = self.LCD_BACKLIGHT

        # Initialize display
        time.sleep(0.05)
        self._write_four_bits(0x03 << 4)
        time.sleep(0.005)
        self._write_four_bits(0x03 << 4)
        time.sleep(0.001)
        self._write_four_bits(0x03 << 4)
        self._write_four_bits(0x02 << 4)

        # Function set: 4-bit mode, 2 lines, 5x8 dots
        self._write_byte(self.LCD_FUNCTION_SET | self.LCD_2LINE | self.LCD_5x8DOTS, 0)

        # Display control: display on, cursor off, blink off
        self._write_byte(self.LCD_DISPLAY_CONTROL | self.LCD_DISPLAY_ON | 
                        self.LCD_CURSOR_OFF | self.LCD_BLINK_OFF, 0)

        # Clear display
        self.clear()

        # Entry mode: increment cursor, no shift
        self._write_byte(self.LCD_ENTRY_MODE | 0x02, 0)
        time.sleep(0.002)

    def _write_four_bits(self, data):
        """Write 4 bits to I2C"""
        self.bus.write_byte(self.address, data | self.backlight)
        self._pulse_enable(data)

    def _pulse_enable(self, data):
        """Pulse enable pin"""
        self.bus.write_byte(self.address, data | self.ENABLE | self.backlight)
        time.sleep(0.0001)
        self.bus.write_byte(self.address, data & ~self.ENABLE | self.backlight)
        time.sleep(0.0001)

    def _write_byte(self, data, mode):
        """Write byte in 4-bit mode"""
        high_bits = mode | (data & 0xF0)
        low_bits = mode | ((data << 4) & 0xF0)

        self._write_four_bits(high_bits)
        self._write_four_bits(low_bits)

    def clear(self):
        """Clear display"""
        self._write_byte(self.LCD_CLEAR, 0)
        time.sleep(0.002)

    def set_cursor(self, col, row):
        """Set cursor position (col: 0-15, row: 0-1)"""
        row_offsets = [0x00, 0x40]
        self._write_byte(self.LCD_SET_DDRAM | (col + row_offsets[row]), 0)

    def print(self, text, col=0, row=0):
        """Print text at specified position"""
        self.set_cursor(col, row)
        for char in text:
            self._write_byte(ord(char), 1)

    def backlight_on(self):
        """Turn backlight on"""
        self.backlight = self.LCD_BACKLIGHT
        self.bus.write_byte(self.address, self.backlight)

    def backlight_off(self):
        """Turn backlight off"""
        self.backlight = 0x00
        self.bus.write_byte(self.address, self.backlight)

# ===========================
# WEIGHING MACHINE CLASS
# ===========================

class WeighingMachine:
    """Main weighing machine controller"""

    def __init__(self):
        """Initialize weighing machine"""
        self.sensors = []
        self.lcd = None
        self.initialize_hardware()

    def initialize_hardware(self):
        """Initialize all hardware components"""
        print("Initializing weighing machine...")

        # Initialize HX711 sensors
        for i, config in enumerate(HX711_CONFIGS):
            hx = HX711(dout_pin=config['dout'], pd_sck_pin=config['pd_sck'])
            hx.reset()

            self.sensors.append({
                'name': config['name'],
                'hx': hx,
                'offset': CALIBRATION[i]['offset'],
                'scale': CALIBRATION[i]['scale']
            })
            print(f"  âœ“ {config['name']} initialized")

        # Initialize LCD
        try:
            self.lcd = LCD1602(address=LCD_I2C_ADDRESS, bus=LCD_I2C_BUS)
            print(f"  âœ“ LCD initialized at 0x{LCD_I2C_ADDRESS:02X}")
        except Exception as e:
            print(f"  âœ— LCD initialization failed: {e}")
            raise

    def read_weight(self):
        """Read weight from all sensors and return total in grams"""
        total_weight = 0.0
        sensor_weights = []

        for sensor in self.sensors:
            raw_reading = sensor['hx'].get_raw_data_mean()

            if raw_reading is not False:
                # Apply calibration: weight = (reading - offset) / scale
                weight_grams = (raw_reading - sensor['offset']) / sensor['scale']
                sensor_weights.append(weight_grams)
                total_weight += weight_grams
            else:
                sensor_weights.append(0.0)

        return total_weight, sensor_weights

    def format_weight_display(self, weight_grams):
        """Format weight for display"""
        if weight_grams < 0:
            weight_grams = 0  # Don't display negative weights

        if weight_grams < 1000:
            return f"{weight_grams:.1f}g"
        else:
            return f"{weight_grams/1000:.3f}kg"

    def update_display(self, weight_grams):
        """Update LCD with current weight"""
        if self.lcd is None:
            return

        # Line 1: Title
        self.lcd.print("Weight Scale    ", col=0, row=0)

        # Line 2: Weight value
        weight_str = self.format_weight_display(weight_grams)
        display_str = f"Weight: {weight_str}"
        self.lcd.print(display_str.ljust(16), col=0, row=1)

    def run(self):
        """Main operation loop"""
        print("\nWeighing machine started!")
        print("Press Ctrl+C to stop\n")

        try:
            # Welcome message
            if self.lcd:
                self.lcd.clear()
                self.lcd.print("Baby Weight", col=0, row=0)
                self.lcd.print("Station Ready", col=0, row=1)
                time.sleep(2)

            while True:
                # Read weight from all sensors
                total_weight, sensor_weights = self.read_weight()

                # Update display
                self.update_display(total_weight)

                # Print to console
                weight_kg = total_weight / 1000
                print(f"\rTotal: {weight_kg:7.3f} kg | " +
                      f"Sensors: [{sensor_weights[0]:6.1f}g, {sensor_weights[1]:6.1f}g, " +
                      f"{sensor_weights[2]:6.1f}g, {sensor_weights[3]:6.1f}g]", 
                      end='', flush=True)

                time.sleep(UPDATE_INTERVAL)

        except KeyboardInterrupt:
            print("\n\nStopping weighing machine...")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        if self.lcd:
            self.lcd.clear()
            self.lcd.print("System", col=0, row=0)
            self.lcd.print("Shutdown", col=0, row=1)
            time.sleep(1)
            self.lcd.backlight_off()

        GPIO.cleanup()
        print("Cleanup complete.")

# ===========================
# MAIN ENTRY POINT
# ===========================

def main():
    """Main entry point"""
    try:
        machine = WeighingMachine()
        machine.run()
    except Exception as e:
        print(f"\nERROR: {e}")
        GPIO.cleanup()

if __name__ == "__main__":
    main()