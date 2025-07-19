from abc import ABC, abstractmethod
from .entities import SensorData,BombaEvent

class SensorDataRepository(ABC):
    @abstractmethod
    def save_sensor_data(self, data: SensorData) -> None:
        pass

class BombaRepository(ABC):
    @abstractmethod
    def save_bomba_activation(self, event: BombaEvent) -> None:
        pass
class MessageQueuePublisher(ABC):
    @abstractmethod
    def publish(self, data: SensorData) -> None:
        pass
