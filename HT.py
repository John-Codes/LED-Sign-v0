from Adafruit_DHTF import Adafruit_DHT
import time

# Set sensor type and GPIO pin
sensor = Adafruit_DHT.DHT11
pin = 4  # GPIO pin number (BCM numbering)

def read_sensor():
    # Try to grab a sensor reading. Use the read_retry method which will retry up to 15 times to
    # get a sensor reading (waiting 2 seconds between each retry).
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    return humidity, temperature

def main():
    while True:
        humidity, temperature = read_sensor()

        # Check if readings are valid
        if humidity is not None and temperature is not None:
            print(f'Temperature: {temperature:.1f}°C, Humidity: {humidity:.1f}%')
        else:
            print('Failed to retrieve data from the sensor')

        # Wait for 2 seconds before the next reading
        time.sleep(2)

if __name__ == "__main__":
    main()