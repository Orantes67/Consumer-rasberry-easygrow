import json
import os
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from easygrow_consumer.domain.entities import SensorData, BombaEvent
from easygrow_consumer.application.services import SensorService, BombaService


class MQTTClient:
    def __init__(self, sensor_service: SensorService, bomba_service: BombaService):
        load_dotenv()
        self.sensor_service = sensor_service
        self.bomba_service = bomba_service

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
            # Suscribirse a ambos tópicos
            self.client.subscribe("sensor/#")
            self.client.subscribe("bomba/estado")
            print("📡 Suscrito a tópicos: sensor/# y bomba/estado")
        else:
            print(f"❌ Error de conexión: código {rc}")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            if topic.startswith("sensor/"):
                # Manejo de datos de sensores (YL-69, DHT22, etc.)
                self._handle_sensor_message(payload)
            elif topic == "bomba/estado":
                # Manejo de eventos de bomba
                self._handle_bomba_message(payload)
            else:
                print(f"⚠️ Tópico no reconocido: {topic}")

        except Exception as e:
            print(f"❌ Error al procesar mensaje en tópico {msg.topic}: {e}")

    def _handle_sensor_message(self, payload):
        """Maneja mensajes de sensores regulares"""
        required_keys = ["mac_address", "valor", "nombre"]
        if not all(k in payload for k in required_keys):
            raise ValueError("❌ JSON incompleto para sensor. Se esperaba mac_address, valor y nombre.")

        data = SensorData(
            mac_address=payload["mac_address"],
            nombre=payload["nombre"],
            valor=payload["valor"]
        )
        self.sensor_service.handle_sensor_data(data)
        print(f"📦 Dato de sensor procesado: {data}")

    def _handle_bomba_message(self, payload):
        """Maneja mensajes de eventos de bomba"""
        required_keys = ["mac_address", "evento", "valor_humedad","id_sensor"]
        if not all(k in payload for k in required_keys):
            raise ValueError("❌ JSON incompleto para bomba. Se esperaba mac_address, evento y valor_humedad.")

        event = BombaEvent(
            mac_address=payload["mac_address"],
            evento=payload["evento"],
            valor_humedad=payload["valor_humedad"],
            tiempo_encendida_seg=payload.get("tiempo_encendida_seg")  # Opcional
        )
        self.bomba_service.handle_bomba_event(event)
        print(f"🔧 Evento de bomba procesado: {event}")

    def start(self):
        self.client.loop_forever()