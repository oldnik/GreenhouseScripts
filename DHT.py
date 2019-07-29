import sys
import Adafruit_DHT
import RPi.GPIO as GPIO

readings = []


def getReadings():
    readings[:] = []
    humidity, temperature = Adafruit_DHT.read(11, 17)
    while humidity is None or temperature is None or humidity > 95:
        humidity, temperature = Adafruit_DHT.read(11, 17)
    return humidity, temperature

