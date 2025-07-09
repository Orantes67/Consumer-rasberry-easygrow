import json
import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from easygrow_consumer.domain.entities import SensorData
from easygrow_consumer.application.services import SensorService


class MQTTClient:
    def __init__(self, service: SensorService):
        load_dotenv()
        self.service = service

        # Cargar variables
        self.host = os.getenv("MOSQUITTOHOST")
        self.username = os.getenv("USERMOSQUITTO")
        self.password = os.getenv("PASSMOSQUITTO")

        if not all([self.host, self.username, self.password]):
            raise ValueError("❌ Faltan variables de entorno MQTT")

        self.client = mqtt.Client()
        self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        try:
            print(f"🔌 Conectando a MQTT broker en {self.host}...")
            self.client.connect(self.host, port=1883, keepalive=60)
        except Exception as e:
            print(f"❌ Error al conectar al broker MQTT: {e}")
            raise e

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Conectado a MQTT broker")
            self.client.subscribe("sensor/#")
        else:
            print(f"❌ Error de conexión: código {rc}")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())

            required_keys = ["mac_address", "valor", "nombre"]
            if not all(k in payload for k in required_keys):
                raise ValueError("❌ JSON incompleto. Se esperaba mac_address, valor y nombre.")

            data = SensorData(
                mac_address=payload["mac_address"],
                nombre=payload["nombre"],
                valor=payload["valor"]
            )
            self.service.handle_sensor_data(data)
            print(f"📦 Dato procesado: {data}")
        except Exception as e:
            print(f"❌ Error al procesar mensaje: {e}")

    def start(self):
        self.client.loop_forever()
