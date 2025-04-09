from typing import Dict, Set
from dataclasses import dataclass

@dataclass
class Station:
    name: str
    lines: Set[str]  # 该站点所属的线路集合
    adjacent_stations: Dict[str, float]  # 相邻站点及距离 {station_name: distance}
    transfer_time: int = 5  # 换乘时间（分钟）
    stop_time: int = 1  # 停站时间（分钟）

    def __init__(self, name: str):
        self.name = name
        self.lines = set()  # 经过该站的线路
        self.adjacent_stations = {}  # 相邻站点及距离

    def add_line(self, line: str):
        self.lines.add(line)

    def add_adjacent_station(self, station_name: str, distance: float):
        self.adjacent_stations[station_name] = distance

    def remove_adjacent_station(self, station_name: str):
        """删除相邻站点"""
        if station_name in self.adjacent_stations:
            del self.adjacent_stations[station_name]

    def update_adjacent_station(self, old_station: str, new_station: str, distance: float):
        """更新相邻站点（将old_station替换为new_station）"""
        if old_station in self.adjacent_stations:
            del self.adjacent_stations[old_station]
            self.adjacent_stations[new_station] = distance

    def remove_line(self, line: str):
        """从站点移除线路"""
        if line in self.lines:
            self.lines.remove(line) 