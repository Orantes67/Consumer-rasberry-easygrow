import os
import json
import pika
import copy # <-- AÑADIDO
from dotenv import load_dotenv
from easygrow_consumer.domain.repository import MessageQueuePublisher
from easygrow_consumer.domain.entities import SensorData, BombaEvent

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

            credentials = pika.PlainCredentials(username=username, password=password)
            parameters = pika.ConnectionParameters(host=host, credentials=credentials)

            print(f"🔌 Conectando a RabbitMQ en {host}...")
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            self.channel.queue_declare(queue=self.sensor_queue, durable=True)
            self.channel.queue_declare(queue=self.bomba_queue, durable=True)
            
            print(f"✅ Conectado correctamente a RabbitMQ")
            print(f"📦 Cola de sensores: '{self.sensor_queue}' creada o verificada")
            print(f"🔧 Cola de bomba: '{self.bomba_queue}' creada o verificada")
            
        except Exception as e:
            print(f"❌ Error al conectar a RabbitMQ: {e}")
            raise e

    def publish(self, data) -> None:
        # Definir la MAC address fija que siempre se va a publicar
        FIXED_MAC_ADDRESS = "D8:3A:DD:1A:5C:B6"

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
            
            # Serializar el mensaje usando el objeto modificado
            message = json.dumps(data_to_publish.__dict__, default=str)
            
            self.channel.basic_publish(
                exchange="",
                routing_key=queue,
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            
            print(f"📤 [{message_type}] Mensaje publicado en cola '{queue}': {message}")
            
        except Exception as e:
            print(f"❌ Error al publicar mensaje: {e}")

    def close(self):
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                print("🔌 Conexión a RabbitMQ cerrada")
        except Exception as e:
            print(f"❌ Error al cerrar conexión RabbitMQ: {e}")