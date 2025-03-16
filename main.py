import time
import ubinascii
from umqtt.simple import MQTTClient
import machine
import random
import ujson as json

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

class BinarySensor(BaseEntity):

    def __init__(self, mqtt, name, object_id, node_id=None,
            discovery_prefix=b'homeassistant', extra_conf=None):

        super().__init__(mqtt, name, b'binary_sensor', object_id, node_id,
                discovery_prefix, extra_conf)

    def publish_state(self, state):
        self.mqtt.publish(self.state_topic, b'ON' if state else b'OFF')
            
    def on(self):
        self.publish_state(True)

    def off(self):
        self.publish_state(False)

class Sensor(BaseEntity):

    def __init__(self, mqtt, name, object_id, node_id=None,
            discovery_prefix=b'homeassistant', extra_conf=None):

        super().__init__(mqtt, name, b'sensor', object_id, node_id,
                discovery_prefix, extra_conf)

class EntityGroup(object):

    def __init__(self, mqtt, node_id, discovery_prefix=b'homeassistant',
            extra_conf=None):
        self.mqtt = mqtt
        self.node_id = node_id
        self.discovery_prefix = discovery_prefix
        # Group wide extra conf, gets passed to sensors
        self.extra_conf = extra_conf
        # Read state_topic from config if provided
        if extra_conf and "state_topic" in extra_conf:
            self.state_topic = extra_conf["state_topic"]
        else:
            self.state_topic = discovery_prefix + b'/sensor/' + node_id + b'/state'
            extra_conf["state_topic"] = self.state_topic
        self.entities = []

    def _update_extra_conf(self, extra_conf):
        if "value_template" not in extra_conf:
            raise Exception("Groupped sensors need value_template to be set.")
        extra_conf.update(self.extra_conf)

    def create_binary_sensor(self, name, object_id, extra_conf):
        self._update_extra_conf(extra_conf)
        bs = BinarySensor(self.mqtt, name, object_id, self.node_id,
                self.discovery_prefix, extra_conf)
        self.entities.append(bs)
        return bs

    def create_sensor(self, name, object_id, extra_conf):
        self._update_extra_conf(extra_conf)
        s = Sensor(self.mqtt, name, object_id, self.node_id,
                self.discovery_prefix, extra_conf)
        self.entities.append(s)
        return s

    def publish_state(self, state):
        self.mqtt.publish(self.state_topic, bytes(json.dumps(state), 'utf-8'))

    def remove_group(self):
        for e in self.entities:
            e.remove_entity()


# Default  MQTT_BROKER to connect to
MQTT_BROKER = "192.168.1.130"
CLIENT_ID = ubinascii.hexlify(machine.unique_id())
PUBLISH_TOPIC = b"homeassistant/sensor/plant_sensor_1/moisture/config"

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
    print(f"Begin connection with MQTT Broker :: {MQTT_BROKER}")
    mqttClient = MQTTClient(CLIENT_ID, MQTT_BROKER, keepalive=60)
    mqttClient.connect()

    print(f"Connected to MQTT  Broker :: {MQTT_BROKER}, and waiting for callback function to be called!")

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

