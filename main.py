from src.easygrow_consumer.infrastructure.bd import PostgresRepository
from src.easygrow_consumer.infrastructure.rabbit_mq_publisher import RabbitMQPublisher
from src.easygrow_consumer.application.services import SensorService, BombaService
from src.easygrow_consumer.infrastructure.mqttclient import MQTTClient

def main():
    try:
        print("🚀 Iniciando EasyGrow Consumer...")
        
        # Inicializar repositorios compartidos
        db_repo = PostgresRepository()
        mq_pub = RabbitMQPublisher()
        
        # Inicializar servicios (ambos usan el mismo publisher)
        sensor_service = SensorService(db_repo, mq_pub)
        bomba_service = BombaService(db_repo, mq_pub)
        
        # Inicializar cliente MQTT con ambos servicios
        mqtt_client = MQTTClient(sensor_service, bomba_service)
        
        print("✅ Todos los servicios iniciados correctamente")
        print("🎯 Escuchando mensajes MQTT...")
        print("📡 Tópicos: sensor/# y bomba/estado")
        print("📦 Colas RabbitMQ: datos_sensores y eventos_bomba")
        
        # Iniciar el loop de MQTT
        mqtt_client.start()
        
    except KeyboardInterrupt:
        print("\n👋 Aplicación detenida por el usuario")
        # Cerrar conexiones limpiamente
        try:
            mq_pub.close()
        except:
            pass
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        raise e

if __name__ == "__main__":
    main()