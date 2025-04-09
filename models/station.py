from typing import Dict, Set
from dataclasses import dataclass

"""地铁站点类，管理单个站点的基本信息和邻接关系"""

@dataclass
class Station:
    name: str
    lines: Set[str]  # 该站点所属的线路集合
    adjacent_stations: Dict[str, float]  # 相邻站点及距离 {station_name: distance}
    transfer_time: int = 5  # 换乘时间（分钟）
    stop_time: int = 1  # 停站时间（分钟）

    def __init__(self, name: str):
        """初始化站点，设置基本属性"""
        self.name = name
        self.lines = set()  # 经过该站的线路
        self.adjacent_stations = {}  # 相邻站点及距离
        self.transfer_time = 5  # 换乘时间（分钟）
        self.stop_time = 1  # 停站时间（分钟）

    def add_line(self, line: str):
        """添加经过该站的线路"""
        self.lines.add(line)

    def add_adjacent_station(self, station_name: str, distance: float):
        """添加相邻站点及距离"""
        self.adjacent_stations[station_name] = distance

    def remove_adjacent_station(self, station_name: str):
        """删除相邻站点"""
        if station_name in self.adjacent_stations:
            del self.adjacent_stations[station_name]  # del: 删除字典中指定的键值对

    def update_adjacent_station(self, old_station: str, new_station: str, distance: float):
        """更新相邻站点信息"""
        if old_station in self.adjacent_stations:
            del self.adjacent_stations[old_station]
            self.adjacent_stations[new_station] = distance

    def remove_line(self, line: str):
        """移除经过该站的线路"""
        if line in self.lines:
            self.lines.remove(line)  # set.remove(): 从集合中移除指定元素 