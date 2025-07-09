from dataclasses import dataclass
from datetime import datetime

@dataclass
class SensorData:
    mac_address: str
    nombre: str
    valor: float
    fecha: datetime = datetime.now()