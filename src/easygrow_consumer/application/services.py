from easygrow_consumer.domain.entities import SensorData, BombaEvent
from easygrow_consumer.domain.repository import SensorDataRepository, BombaRepository, MessageQueuePublisher

class SensorService:
    def __init__(self, repository: SensorDataRepository, publisher: MessageQueuePublisher):
        self.repository = repository
        self.publisher = publisher

    def handle_sensor_data(self, data: SensorData):
        self.repository.save_sensor_data(data)
        self.publisher.publish(data)

class BombaService:
    def __init__(self, repository: BombaRepository, publisher: MessageQueuePublisher):
        self.repository = repository
        self.publisher = publisher

    def handle_bomba_event(self, event: BombaEvent):
        print(f"🔧 Procesando evento: {event.evento}")
        print(f"🔍 Tiempo encendida: {event.tiempo_encendida_seg}")
        
        # SOLO guardar en BD cuando la bomba se DESACTIVA (tiene tiempo de encendido)
        if event.tiempo_encendida_seg is not None and event.tiempo_encendida_seg > 0:
            print(f"💾 Guardando activación en BD (bomba desactivada)")
            self.repository.save_bomba_activation(event)
        else:
            print(f"ℹ️ Evento de activación - NO se guarda en BD (solo se publica)")
        
        # Publicar TODOS los eventos a RabbitMQ
        self.publisher.publish(event)
        print(f"📤 Evento publicado a RabbitMQ: {event.evento}")