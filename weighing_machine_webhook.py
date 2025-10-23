#!/usr/bin/env python3
"""
weighing_machine_webhook.py - Weighing Machine with Webhook Integration
Extended version with HTTP webhook support for IoT/cloud integration.
Sends weight data to a configurable webhook endpoint at regular intervals.
"""

import time
import json
import requests
from datetime import datetime
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

# Webhook Configuration
WEBHOOK_ENABLED = False  # Set to True to enable webhook
WEBHOOK_URL = "https://your-webhook-endpoint.com/api/weight"  # Your webhook URL
DEVICE_ID = "pi_zero_scale_001"  # Unique device identifier
SEND_INTERVAL = 5  # Seconds between webhook transmissions

# Update interval (seconds)
UPDATE_INTERVAL = 0.5

# ===========================
# LCD1602 I2C DRIVER
# ===========================

class LCD1602:
    """Driver for LCD1602 with I2C interface"""

    LCD_CLEAR = 0x01
    LCD_HOME = 0x02
    LCD_ENTRY_MODE = 0x04
    LCD_DISPLAY_CONTROL = 0x08
    LCD_FUNCTION_SET = 0x20
    LCD_SET_DDRAM = 0x80
    LCD_DISPLAY_ON = 0x04
    LCD_CURSOR_OFF = 0x00
    LCD_BLINK_OFF = 0x00
    LCD_2LINE = 0x08
    LCD_5x8DOTS = 0x00
    LCD_BACKLIGHT = 0x08
    ENABLE = 0b00000100

    def __init__(self, address=0x27, bus=1):
        self.address = address
        self.bus = smbus2.SMBus(bus)
        self.backlight = self.LCD_BACKLIGHT

        time.sleep(0.05)
        self._write_four_bits(0x03 << 4)
        time.sleep(0.005)
        self._write_four_bits(0x03 << 4)
        time.sleep(0.001)
        self._write_four_bits(0x03 << 4)
        self._write_four_bits(0x02 << 4)

        self._write_byte(self.LCD_FUNCTION_SET | self.LCD_2LINE | self.LCD_5x8DOTS, 0)
        self._write_byte(self.LCD_DISPLAY_CONTROL | self.LCD_DISPLAY_ON | 
                        self.LCD_CURSOR_OFF | self.LCD_BLINK_OFF, 0)
        self.clear()
        self._write_byte(self.LCD_ENTRY_MODE | 0x02, 0)
        time.sleep(0.002)

    def _write_four_bits(self, data):
        self.bus.write_byte(self.address, data | self.backlight)
        self._pulse_enable(data)

    def _pulse_enable(self, data):
        self.bus.write_byte(self.address, data | self.ENABLE | self.backlight)
        time.sleep(0.0001)
        self.bus.write_byte(self.address, data & ~self.ENABLE | self.backlight)
        time.sleep(0.0001)

    def _write_byte(self, data, mode):
        high_bits = mode | (data & 0xF0)
        low_bits = mode | ((data << 4) & 0xF0)
        self._write_four_bits(high_bits)
        self._write_four_bits(low_bits)

    def clear(self):
        self._write_byte(self.LCD_CLEAR, 0)
        time.sleep(0.002)

    def set_cursor(self, col, row):
        row_offsets = [0x00, 0x40]
        self._write_byte(self.LCD_SET_DDRAM | (col + row_offsets[row]), 0)

    def print(self, text, col=0, row=0):
        self.set_cursor(col, row)
        for char in text:
            self._write_byte(ord(char), 1)

    def backlight_on(self):
        self.backlight = self.LCD_BACKLIGHT
        self.bus.write_byte(self.address, self.backlight)

    def backlight_off(self):
        self.backlight = 0x00
        self.bus.write_byte(self.address, self.backlight)

# ===========================
# WEIGHING MACHINE CLASS
# ===========================

class WeighingMachineWithWebhook:
    """Weighing machine with webhook support"""

    def __init__(self):
        self.sensors = []
        self.lcd = None
        self.last_webhook_time = 0
        self.webhook_counter = 0
        self.initialize_hardware()

    def initialize_hardware(self):
        """Initialize all hardware components"""
        print("Initializing weighing machine with webhook support...")

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

        # Webhook status
        if WEBHOOK_ENABLED:
            print(f"  âœ“ Webhook enabled: {WEBHOOK_URL}")
        else:
            print("  â„¹ Webhook disabled")

    def read_weight(self):
        """Read weight from all sensors"""
        total_weight = 0.0
        sensor_weights = []

        for sensor in self.sensors:
            raw_reading = sensor['hx'].get_raw_data_mean()

            if raw_reading is not False:
                weight_grams = (raw_reading - sensor['offset']) / sensor['scale']
                sensor_weights.append(weight_grams)
                total_weight += weight_grams
            else:
                sensor_weights.append(0.0)

        return total_weight, sensor_weights

    def send_webhook(self, total_weight, sensor_weights):
        """Send weight data to webhook endpoint"""
        if not WEBHOOK_ENABLED:
            return

        try:
            # Prepare payload
            payload = {
                "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "total_weight_grams": round(total_weight, 2),
                "total_weight_kg": round(total_weight / 1000, 3),
                "sensors": [
                    {"sensor": f"sensor_{i+1}", "weight_grams": round(w, 2)}
                    for i, w in enumerate(sensor_weights)
                ],
                "device_id": DEVICE_ID
            }

            # Send POST request
            response = requests.post(
                WEBHOOK_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )

            if response.status_code == 200:
                self.webhook_counter += 1
                print(f"  [Webhook #{self.webhook_counter}] Sent successfully")
            else:
                print(f"  [Webhook] Failed: HTTP {response.status_code}")

        except requests.exceptions.Timeout:
            print("  [Webhook] Timeout error")
        except requests.exceptions.RequestException as e:
            print(f"  [Webhook] Error: {e}")

    def format_weight_display(self, weight_grams):
        """Format weight for display"""
        if weight_grams < 0:
            weight_grams = 0

        if weight_grams < 1000:
            return f"{weight_grams:.1f}g"
        else:
            return f"{weight_grams/1000:.3f}kg"

    def update_display(self, weight_grams):
        """Update LCD with current weight"""
        if self.lcd is None:
            return

        self.lcd.print("Weight Scale    ", col=0, row=0)
        weight_str = self.format_weight_display(weight_grams)
        display_str = f"Weight: {weight_str}"
        self.lcd.print(display_str.ljust(16), col=0, row=1)

    def run(self):
        """Main operation loop"""
        print("\nWeighing machine started with webhook support!")
        print("Press Ctrl+C to stop\n")

        try:
            # Welcome message
            if self.lcd:
                self.lcd.clear()
                self.lcd.print("Baby Weight", col=0, row=0)
                self.lcd.print("IoT Ready", col=0, row=1)
                time.sleep(2)

            while True:
                current_time = time.time()

                # Read weight from all sensors
                total_weight, sensor_weights = self.read_weight()

                # Update display
                self.update_display(total_weight)

                # Send webhook if interval elapsed
                if WEBHOOK_ENABLED and (current_time - self.last_webhook_time) >= SEND_INTERVAL:
                    self.send_webhook(total_weight, sensor_weights)
                    self.last_webhook_time = current_time

                # Print to console
                weight_kg = total_weight / 1000
                webhook_status = f"[WH: {self.webhook_counter}]" if WEBHOOK_ENABLED else ""
                print(f"\r{webhook_status} Total: {weight_kg:7.3f} kg | " +
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
        machine = WeighingMachineWithWebhook()
        machine.run()
    except Exception as e:
        print(f"\nERROR: {e}")
        GPIO.cleanup()

if __name__ == "__main__":
    main()