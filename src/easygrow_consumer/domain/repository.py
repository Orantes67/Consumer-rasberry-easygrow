from abc import ABC, abstractmethod
from .entities import SensorData

class SensorDataRepository(ABC):
    @abstractmethod
    def save_sensor_data(self, data: SensorData) -> None:
        pass

class MessageQueuePublisher(ABC):
    @abstractmethod
    def publish(self, data: SensorData) -> None:
        pass
