#create a BACnet virtual device with a temperature sensor object
from bacpypes.core import run, stop
from bacpypes.app import BIPSimpleApplication
from bacpypes.object import AnalogValueObject
from bacpypes.local.device import LocalDeviceObject
from bacpypes.pdu import Address
from bacpypes.service.device import WhoIsIAmServices
import random
# Define the BACnet device
this_device = LocalDeviceObject(
    objectName="VirtualTemperatureSensor",
    objectIdentifier=1234,
    maxApduLengthAccepted=1024,
    segmentationSupported="noSegmentation",
    vendorIdentifier=15
)
# Create the BACnet application
this_application = BIPSimpleApplication(this_device, Address("192.168.0.25"))
# Add Who-Is/I-Am services
this_application.add_capability(WhoIsIAmServices)
# Create an Analog Value Object to represent the temperature sensor
temperature_sensor = AnalogValueObject(
    objectIdentifier=("analogValue", 1),
    objectName="TemperatureSensor1",
    presentValue=22.0,  # Initial temperature value
    units="degreesCelsius"
)
# Add the temperature sensor object to the application
this_application.add_object(temperature_sensor)
# Function to update the temperature value periodically
def update_temperature():
    new_temp = round(random.uniform(20.0, 25.0), 2)  # Simulate temperature change
    temperature_sensor.presentValue = new_temp
    print(f"Updated Temperature: {new_temp} °C")
    # Schedule the next update
    from bacpypes.core import deferred
    deferred(5, update_temperature)  # Update every 5 seconds
# Start the temperature update loop
update_temperature()
run()
# To stop the application gracefully, you can call stop() when needed
# stop()