"""
數據模型模組 - 定義所有 API 的資料結構
"""
from .bus_models import (
    BusRoute,
    BusTimeEntry,
    BusRealTimeArrival,
    BusStop,
    BusVehicle,
    BusRouteData,
)
from .railway_models import TrainStation, TrainTimeEntry
from .thsr_models import THSRStation, THSRTrainEntry

__all__ = [
    "BusRoute",
    "BusTimeEntry",
    "BusRealTimeArrival",
    "BusStop",
    "BusVehicle",
    "BusRouteData",
    "TrainStation",
    "TrainTimeEntry",
    "THSRStation",
    "THSRTrainEntry",
]
