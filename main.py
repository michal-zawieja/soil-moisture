import time
import ubinascii
from umqtt.simple import MQTTClient
import machine
import random
import ujson as json
import network
import config

# WiFi configuration
SSID = config.SSID
PASSWORD = config.PASSWORD
# Default  MQTT_BROKER to connect to
MQTT_BROKER = config.MQTT_BROKER
PUBLISH_TOPIC = config.PUBLISH_TOPIC
CLIENT_ID = ubinascii.hexlify(machine.unique_id())

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    
    print(f"Connecting to WiFi network: {SSID}")
    while not wlan.isconnected():
        time.sleep(1)
        print("Waiting for connection...")
    
    print("Connected to WiFi")
    print("Network config:", wlan.ifconfig())

class BaseEntity(object):

    def __init__(self, mqtt, name, component, object_id, node_id, discovery_prefix, extra_conf):
        self.mqtt = mqtt

        base_topic = discovery_prefix + b'/' + component + b'/'
        if node_id:
            base_topic += node_id + b'/'
        base_topic += object_id + b'/'

        self.config_topic = base_topic + b'config'
        self.state_topic = base_topic + b'state'

        self.config = {"name": name, "state_topic": self.state_topic}
        if extra_conf:
            self.config.update(extra_conf)
        self.mqtt.publish(self.config_topic, bytes(json.dumps(self.config), 'utf-8'), True, 1)

    def remove_entity(self):
        self.mqtt.publish(self.config_topic, b'', 1)

    def publish_state(self, state):
        self.mqtt.publish(self.state_topic, state)

class Sensor(BaseEntity):

    def __init__(self, mqtt, name, object_id, node_id=None,
            discovery_prefix=b'homeassistant', extra_conf=None):

        super().__init__(mqtt, name, b'sensor', object_id, node_id,
                discovery_prefix, extra_conf)

# Setup built in PICO LED as Output
led = machine.Pin("LED",machine.Pin.OUT)

# Publish MQTT messages after every set timeout
last_publish = time.time()
publish_interval = 5

def reset():
    print("Resetting...")
    time.sleep(5)
    machine.reset()
    
# Generate dummy random temperature readings    
def get_moisture_reading():
    return random.randint(20, 50)
    
def main():
    connect_wifi()

    print(f"Begin connection with MQTT Broker :: {MQTT_BROKER}")
    mqttClient = MQTTClient(CLIENT_ID, MQTT_BROKER, keepalive=60)
    mqttClient.connect()

    print(f"Connected to MQTT  Broker :: {MQTT_BROKER}!")

    temp_config = { "unit_of_measurement": "%", "device_class": "moisture" }
    temp = Sensor(mqttClient, b"moisture_sensor", b"sensorid", extra_conf=temp_config)

    while True:
            random_moisture = get_moisture_reading()
            temp.publish_state(str(random_moisture))
            time.sleep(publish_interval)

if __name__ == "__main__":
    while True:
        try:
            main()
        except OSError as e:
            print("Error: " + str(e))
            reset()
