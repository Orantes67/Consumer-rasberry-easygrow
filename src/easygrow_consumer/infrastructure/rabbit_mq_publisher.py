import os
import json
import pika
import copy # <-- AÑADIDO
from dotenv import load_dotenv
from src.easygrow_consumer.domain.repository import MessageQueuePublisher
from src.easygrow_consumer.domain.entities import SensorData, BombaEvent

class RabbitMQPublisher(MessageQueuePublisher):
    def __init__(self):
        load_dotenv()
        
        self.sensor_queue = os.getenv("RABBITMQ_SENSOR_QUEUE", "datos_sensores")
        self.bomba_queue = os.getenv("RABBITMQ_BOMBA_QUEUE", "eventos_bomba")
        
        try:
            username = os.getenv("RABBITMQ_USER")
            password = os.getenv("RABBITMQ_PASSWORD")
            host = os.getenv("RABBITMQ_HOST")

            if not all([username, password, host]):
                raise ValueError("❌ Faltan variables de entorno para RabbitMQ")

            # Guardar parámetros para posibles reconexiones
            self.username = username
            self.password = password
            self.host = host
            self.credentials = pika.PlainCredentials(username=username, password=password)
            self.parameters = pika.ConnectionParameters(host=host, credentials=self.credentials, heartbeat=600, blocked_connection_timeout=300)

            print(f"🔌 Conectando a RabbitMQ en {host}...")
            self._connect()

            print(f"✅ Conectado correctamente a RabbitMQ")
            print(f"📦 Cola de sensores: '{self.sensor_queue}' creada o verificada")
            print(f"🔧 Cola de bomba: '{self.bomba_queue}' creada o verificada")

        except Exception as e:
            print(f"❌ Error al conectar a RabbitMQ: {e}")
            raise e

    def publish(self, data) -> None:
        # Definir la MAC address fija que siempre se va a publicar
        FIXED_MAC_ADDRESS = "d8:3a:dd:1a:5c:b5"

        try:
            if isinstance(data, SensorData):
                queue = self.sensor_queue
                message_type = "SENSOR"
            elif isinstance(data, BombaEvent):
                queue = self.bomba_queue
                message_type = "BOMBA"
            else:
                raise ValueError(f"❌ Tipo de dato no soportado: {type(data)}")

            # Crear una copia profunda para no alterar el objeto original
            data_to_publish = copy.deepcopy(data)
            # Sobrescribir la dirección MAC en la copia
            data_to_publish.mac_address = FIXED_MAC_ADDRESS
            
            # Serializar el mensaje con fecha en formato ISO completo (incluye microsegundos)
            def serialize_datetime(obj):
                # Importar datetime en la función para evitar conflicto de nombres
                from datetime import datetime as dt
                if isinstance(obj, dt):
                    return obj.isoformat()  # Formato: "2025-12-02T10:31:45.126058"
                return str(obj)
            
            message = json.dumps(data_to_publish.__dict__, default=serialize_datetime)
            
            # Verificar que la conexión y el canal estén abiertos
            if not hasattr(self, 'connection') or self.connection.is_closed:
                print("⚠️ Conexión cerrada, intentando reconectar a RabbitMQ...")
                self._connect()

            if not hasattr(self, 'channel') or self.channel.is_closed:
                print("⚠️ Canal cerrado, intentando abrir un nuevo canal...")
                self.channel = self.connection.channel()
                # Asegurarse de que las colas sigan existiendo
                self.channel.queue_declare(queue=self.sensor_queue, durable=True)
                self.channel.queue_declare(queue=self.bomba_queue, durable=True)

            self.channel.basic_publish(
                exchange="",
                routing_key=queue,
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )

            print(f"📤 [{message_type}] Mensaje publicado en cola '{queue}': {message}")

        except Exception as e:
            # Mostrar error y propagar para registro superior
            print(f"❌ Error al publicar mensaje: {e}")
            raise

    def close(self):
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                print("🔌 Conexión a RabbitMQ cerrada")
        except Exception as e:
            print(f"❌ Error al cerrar conexión RabbitMQ: {e}")

    def _connect(self):
        """Realiza la conexión a RabbitMQ y declara las colas usadas."""
        # Intentos simples de reconexión
        attempts = 3
        last_exc = None
        for i in range(attempts):
            try:
                self.connection = pika.BlockingConnection(self.parameters)
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.sensor_queue, durable=True)
                self.channel.queue_declare(queue=self.bomba_queue, durable=True)
                return
            except Exception as e:
                print(f"⚠️ Intento {i+1}/{attempts} fallo al conectar a RabbitMQ: {e}")
                last_exc = e
        # Si no se pudo conectar, lanzar la última excepción
        raise last_exc