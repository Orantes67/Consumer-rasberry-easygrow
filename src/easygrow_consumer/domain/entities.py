from dataclasses import dataclass
from datetime import datetime
from typing import Optional
@dataclass
class SensorData:
    mac_address: str
    nombre: str
    valor: float
    fecha: datetime = datetime.now()

@dataclass
class BombaEvent:
    mac_address: str
    evento: str
    id_sensor: int
    valor_humedad: float
    tiempo_encendida_seg: Optional[int] = None
    fecha: datetime = datetime.now()