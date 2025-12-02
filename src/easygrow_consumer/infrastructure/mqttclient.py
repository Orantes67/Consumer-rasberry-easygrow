import json
import os
import time
import logging
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from src.easygrow_consumer.domain.entities import SensorData, BombaEvent
from src.easygrow_consumer.application.services import SensorService, BombaService


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

        # Logger
        self.logger = logging.getLogger("easygrow.mqtt")

        # Cliente MQTT
        self.client = mqtt.Client()
        self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        # Configurar reintentos controlados por cliente
        try:
            # ajustes de reconexión de la librería
            self.client.reconnect_delay_set(min_delay=1, max_delay=120)

            self.logger.info(f"🔌 Conectando a MQTT broker en {self.host}...")
            # No bloqueamos aquí: conectamos y dejaremos el loop activo en start()
            self.client.connect(self.host, port=1883, keepalive=60)
            self.connected = False
        except Exception as e:
            self.logger.exception(f"❌ Error al conectar al broker MQTT: {e}")
            raise e

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("✅ Conectado a MQTT broker")
            self.connected = True
            # Suscribirse a ambos tópicos
            self.client.subscribe("sensor/#")
            self.client.subscribe("bomba/estado")
            self.logger.info("📡 Suscrito a tópicos: sensor/# y bomba/estado")
        else:
            self.logger.error(f"❌ Error de conexión: código {rc}")

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
                self.logger.warning(f"⚠️ Tópico no reconocido: {topic}")

        except Exception as e:
            self.logger.exception(f"❌ Error al procesar mensaje en tópico {msg.topic}: {e}")

    def _handle_sensor_message(self, payload):
        """Maneja mensajes de sensores regulares"""
        from datetime import datetime
        required_keys = ["mac_address", "valor", "nombre"]
        if not all(k in payload for k in required_keys):
            raise ValueError("❌ JSON incompleto para sensor. Se esperaba mac_address, valor y nombre.")

        data = SensorData(
            mac_address=payload["mac_address"],
            nombre=payload["nombre"],
            valor=payload["valor"],
            fecha=datetime.now()  # Capturar fecha justo al procesar el mensaje
        )
        try:
            self.sensor_service.handle_sensor_data(data)
            self.logger.info(f"📦 Dato de sensor procesado: {data}")
        except Exception:
            self.logger.exception("❌ Error procesando dato de sensor")

    def _handle_bomba_message(self, payload):
        """Maneja mensajes de eventos de bomba"""
        from datetime import datetime
        required_keys = ["mac_address", "evento", "valor_humedad","id_sensor"]
        if not all(k in payload for k in required_keys):
            raise ValueError("❌ JSON incompleto para bomba. Se esperaba mac_address, evento, valor_humedad e id_sensor.")

        event = BombaEvent(
            mac_address=payload["mac_address"],
            evento=payload["evento"],
            id_sensor=payload["id_sensor"],
            valor_humedad=payload["valor_humedad"],
            tiempo_encendida_seg=payload.get("tiempo_encendida_seg"),  # Opcional
            fecha=datetime.now()  # Capturar fecha justo al procesar el mensaje
        )
        try:
            self.bomba_service.handle_bomba_event(event)
            self.logger.info(f"🔧 Evento de bomba procesado: {event}")
        except Exception:
            self.logger.exception("❌ Error procesando evento de bomba")

    def on_disconnect(self, client, userdata, rc):
        # rc == 0 means a clean disconnect
        self.connected = False
        if rc == 0:
            self.logger.info("🔌 Desconectado del broker MQTT limpiamente")
        else:
            self.logger.warning(f"⚠️ Desconexión inesperada del broker MQTT (rc={rc})")

    def start(self):
        """Inicia el loop MQTT en background y supervisa la conexión para reconectar si es necesario."""
        self.client.loop_start()
        try:
            while True:
                # Si no estamos conectados, intentamos reconectar periódicamente
                if not getattr(self, 'connected', False):
                    try:
                        self.logger.info("Intentando reconectar al broker MQTT...")
                        self.client.reconnect()
                        # si reconnect no lanza, dejaremos que on_connect marque el estado
                    except Exception as e:
                        self.logger.warning(f"Reconexión fallida: {e}")
                time.sleep(2)
        except KeyboardInterrupt:
            self.logger.info("Deteniendo cliente MQTT por KeyboardInterrupt")
        finally:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass