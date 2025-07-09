import os
import json
import pika
from dotenv import load_dotenv
from easygrow_consumer.domain.repository import MessageQueuePublisher
from easygrow_consumer.domain.entities import SensorData

class RabbitMQPublisher(MessageQueuePublisher):
    def __init__(self):
        load_dotenv()
        self.queue = os.getenv("RABBITMQ_QUEUE", "datos_sensores")
        try:
            # Leer credenciales
            username = os.getenv("RABBITMQ_USER")
            password = os.getenv("RABBITMQ_PASSWORD")
            host = os.getenv("RABBITMQ_HOST")

            # Validar datos
            if not all([username, password, host]):
                raise ValueError("❌ Faltan variables de entorno para RabbitMQ")

            # Credenciales y conexión
            credentials = pika.PlainCredentials(username=username, password=password)
            parameters = pika.ConnectionParameters(host=host, credentials=credentials)

            print(f"🔌 Conectando a RabbitMQ en {host}...")
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue, durable=True)
            print(f"✅ Conectado correctamente a RabbitMQ y cola '{self.queue}' creada o verificada.")
        except Exception as e:
            print(f"❌ Error al conectar a RabbitMQ: {e}")
            raise e  # Detener ejecución si no se pudo conectar

    def publish(self, data: SensorData) -> None:
        try:
            message = json.dumps(data.__dict__, default=str)
            self.channel.basic_publish(
                exchange="",
                routing_key=self.queue,
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )
            print(f"📤 Mensaje publicado en RabbitMQ: {message}")
        except Exception as e:
            print(f"❌ Error al publicar mensaje: {e}")
