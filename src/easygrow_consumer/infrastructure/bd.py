import os
import psycopg2
from dotenv import load_dotenv
from easygrow_consumer.domain.repository import SensorDataRepository, BombaRepository
from easygrow_consumer.domain.entities import SensorData, BombaEvent

class PostgresRepository(SensorDataRepository, BombaRepository):
    def __init__(self):
        load_dotenv()
        try:
            self.conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASS"),
                dbname=os.getenv("DB_SCHEMA")
            )
            self.conn.autocommit = True
            print("✅ Conexión exitosa a PostgreSQL")
        except Exception as e:
            print(f"❌ Error al conectar a PostgreSQL: {e}")
            raise e

    def save_sensor_data(self, data: SensorData):
        with self.conn.cursor() as cur:
            # Buscar el id_sensor con la descripción y la mac_address
            cur.execute(
                """
                SELECT s.id_sensor
                FROM sensores s
                JOIN dispositivos d ON s.id_dispositivo = d.id_dispositivo
                WHERE s.descripcion = %s AND d.mac_address = %s
                """,
                (data.nombre, data.mac_address)
            )

            sensor_row = cur.fetchone()

            if sensor_row:
                id_sensor = sensor_row[0]
                cur.execute(
                    """
                    INSERT INTO datos_sensores (id_sensor, mac_address, valor, fecha)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (id_sensor, data.mac_address, data.valor, data.fecha)
                )
                print(f"✅ Dato guardado para sensor ID {id_sensor}")
            else:
                print(f"⚠️ No se encontró el sensor con nombre '{data.nombre}' y MAC '{data.mac_address}'.")

    def save_bomba_activation(self, event: BombaEvent):
        print(f"🔍 Guardando activación de bomba para MAC: {event.mac_address}")
        print(f"🔍 Duración: {event.tiempo_encendida_seg} segundos")
        
        with self.conn.cursor() as cur:
            try:
                # Ya no buscamos el id_sensor, lo usamos directamente
                cur.execute(
                    """
                    INSERT INTO activaciones_bombas (id_sensor, mac_address, fecha, duracion_segundos)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (event.id_sensor, event.mac_address, event.fecha, event.tiempo_encendida_seg)
                )
                print(f"✅ Activación guardada - Sensor ID: {event.id_sensor}, Duración: {event.tiempo_encendida_seg}s")

                # Verificar que se guardó
                cur.execute("SELECT COUNT(*) FROM activaciones_bombas WHERE id_sensor = %s", (event.id_sensor,))
                count = cur.fetchone()[0]
                print(f"📊 Total activaciones para sensor {event.id_sensor}: {count}")

            except Exception as e:
                print(f"❌ Error al guardar activación de bomba: {e}")
                import traceback
                traceback.print_exc()