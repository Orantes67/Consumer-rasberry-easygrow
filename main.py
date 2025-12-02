import sys
import os
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.easygrow_consumer.infrastructure.bd import PostgresRepository
from src.easygrow_consumer.infrastructure.rabbit_mq_publisher import RabbitMQPublisher
from src.easygrow_consumer.application.services import SensorService, BombaService
from src.easygrow_consumer.infrastructure.mqttclient import MQTTClient


# Configurar logging con timestamps y niveles
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("easygrow.main")


def main():
    logger.info("🚀 Iniciando EasyGrow Consumer...")

    db_repo = None
    mq_pub = None
    sensor_service = None
    bomba_service = None
    mqtt_client = None

    try:
        # Inicializar repositorios compartidos
        try:
            logger.info("Conectando a PostgreSQL...")
            db_repo = PostgresRepository()
            logger.info("✅ Conexión a PostgreSQL establecida")
        except Exception:
            logger.exception("❌ Falló la conexión a PostgreSQL")
            raise

        try:
            logger.info("Inicializando RabbitMQ publisher...")
            mq_pub = RabbitMQPublisher()
            logger.info("✅ RabbitMQ publisher inicializado")
        except Exception:
            logger.exception("❌ Falló la inicialización de RabbitMQPublisher")
            raise

        # Inicializar servicios (ambos usan el mismo publisher)
        try:
            logger.info("Creando servicios de aplicación (Sensor y Bomba)...")
            sensor_service = SensorService(db_repo, mq_pub)
            bomba_service = BombaService(db_repo, mq_pub)
            logger.info("✅ Servicios creados correctamente")
        except Exception:
            logger.exception("❌ Error al crear los servicios SensorService/BombaService")
            raise

        # Inicializar cliente MQTT con ambos servicios
        try:
            logger.info("Inicializando cliente MQTT...")
            mqtt_client = MQTTClient(sensor_service, bomba_service)
            logger.info("✅ Cliente MQTT creado")
        except Exception:
            logger.exception("❌ Error al inicializar MQTTClient")
            raise

        logger.info("🎯 Preparado para escuchar mensajes MQTT")
        logger.info("📡 Tópicos: sensor/# y bomba/estado")
        logger.info("📦 Colas RabbitMQ: datos_sensores y eventos_bomba")

        # Iniciar el loop de MQTT
        try:
            logger.info("Iniciando bucle MQTT (start)...")
            mqtt_client.start()
            logger.info("MQTT loop finalizado (start retornó)")
        except KeyboardInterrupt:
            logger.info("\n👋 Aplicación detenida por el usuario (KeyboardInterrupt)")
        except Exception:
            logger.exception("❌ Excepción durante mqtt_client.start()")
            raise

    except Exception:
        logger.error("La aplicación terminó debido a un error crítico. Revisa los logs para más detalles")
        # Intentar cerrar conexiones si existen
        try:
            if mq_pub:
                mq_pub.close()
                logger.info("RabbitMQ publisher cerrado")
        except Exception:
            logger.exception("Error cerrando RabbitMQ publisher")

        try:
            if db_repo and hasattr(db_repo, 'conn'):
                try:
                    db_repo.conn.close()
                    logger.info("Conexión a PostgreSQL cerrada")
                except Exception:
                    logger.exception("Error cerrando conexión a PostgreSQL")
        except Exception:
            logger.exception("Error al intentar limpiar recursos de BD")

        # Salir con código de error
        sys.exit(1)


if __name__ == "__main__":
    main()