
from src.easygrow_consumer.infrastructure.bd import PostgresRepository
from src.easygrow_consumer.infrastructure.rabbit_mq_publisher import RabbitMQPublisher
from src.easygrow_consumer.application.services import SensorService
from src.easygrow_consumer.infrastructure.mqttclient import MQTTClient

if __name__ == "__main__":

    db_repo = PostgresRepository()
    mq_pub = RabbitMQPublisher()
    service = SensorService(db_repo, mq_pub)
    mqtt_client = MQTTClient(service)
    mqtt_client.start()
