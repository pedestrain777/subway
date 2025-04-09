from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Line:
    line_id: str  # 线路编号
    start_times: Dict[str, str]  # 不同始发站的发车时间 {station_name: time}
    speed: float  # 线路速度（km/h）
    stations: List[str]  # 正向站点列表
    reverse_stations: List[str]  # 反向站点列表
    
    def __init__(self, line_id: str, speed: float):
        self.line_id = line_id
        self.speed = speed
        self.start_times = {}
        self.stations = []
        self.reverse_stations = []

    def add_start_time(self, station: str, time: str):
        self.start_times[station] = time

    def set_stations(self, stations: List[str]):
        self.stations = stations
        self.reverse_stations = stations[::-1]

    def add_station(self, new_station: str, prev_station: str, next_station: str):
        """在两个相邻站点之间添加新站点"""
        if prev_station not in self.stations or next_station not in self.stations:
            raise ValueError("前后站点必须在当前线路中")
        
        # 确保prev_station和next_station是相邻的
        prev_idx = self.stations.index(prev_station)
        next_idx = self.stations.index(next_station)
        if abs(prev_idx - next_idx) != 1:
            raise ValueError("指定的站点不相邻")
        
        # 在正向站点列表中插入新站点
        insert_idx = max(prev_idx, next_idx)
        self.stations.insert(insert_idx, new_station)
        # 更新反向站点列表
        self.reverse_stations = self.stations[::-1]

    def remove_station(self, station: str):
        """从线路中删除站点"""
        if station in self.stations:
            self.stations.remove(station)
            self.reverse_stations = self.stations[::-1]

    def extend_line(self, new_station: str, terminal_station: str):
        """延长线路（在终点站后添加新站点）"""
        if terminal_station not in [self.stations[0], self.stations[-1]]:
            raise ValueError("只能在终点站延长线路")
        
        if terminal_station == self.stations[0]:
            self.stations.insert(0, new_station)
        else:
            self.stations.append(new_station)
        
        self.reverse_stations = self.stations[::-1] 