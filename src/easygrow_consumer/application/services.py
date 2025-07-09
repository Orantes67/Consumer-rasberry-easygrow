from easygrow_consumer.domain.entities import SensorData
from easygrow_consumer.domain.repository import SensorDataRepository, MessageQueuePublisher

class SensorService:
    def __init__(self, repository: SensorDataRepository, publisher: MessageQueuePublisher):
        self.repository = repository
        self.publisher = publisher

    def handle_sensor_data(self, data: SensorData):
        self.repository.save_sensor_data(data)
        self.publisher.publish(data)