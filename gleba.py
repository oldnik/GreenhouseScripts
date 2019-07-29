import smbus
import time

devAddress = 0x48
A0 = 0x42
RESOLUTION = 255
VOLTAGE = 3.3

i2cBus = smbus.SMBus(1)


def getData(channel):
	i2cBus.write_byte(devAddress, channel)
	readValue = i2cBus.read_byte(devAddress)
	convert = (readValue * VOLTAGE / RESOLUTION)
	return convert

def mapa(value, fromLow, fromHigh, toLow, toHigh):
	return (value - fromLow) * (toHigh - toLow) / (fromHigh - fromLow) + toLow

def getReadings():
	return mapa(getData(A0), 0.8, 3.3, 100, 0)

