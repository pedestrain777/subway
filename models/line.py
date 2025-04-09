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
        """初始化线路
        Args:
            line_id: 线路编号
            speed: 最高时速（公里/小时），将自动转换为平均速度
        """
        self.line_id = line_id
        self.speed = speed / 2  # 将最高时速转换为平均速度
        self.start_times = {}
        self.stations = []
        self.reverse_stations = []

    def add_start_time(self, station: str, time: str):
        self.start_times[station] = time

    def set_stations(self, stations: List[str]):
        self.stations = stations
        self.reverse_stations = stations[::-1]

    def add_station(self, station: str, prev_station: str = None, next_station: str = None):
        """添加站点到线路中"""
        if not self.stations:
            self.stations.append(station)
            return
            
        if prev_station and next_station:
            try:
                prev_index = self.stations.index(prev_station)
                next_index = self.stations.index(next_station)
                if abs(prev_index - next_index) != 1:
                    raise ValueError("相邻站点必须连续")
                insert_index = max(prev_index, next_index)
                self.stations.insert(insert_index, station)
            except ValueError:
                raise ValueError("指定的相邻站点不在线路上")
        else:
            self.stations.append(station)

    def remove_station(self, station: str):
        """从线路中移除站点"""
        if station in self.stations:
            self.stations.remove(station)
            self.reverse_stations = self.stations[::-1]
        else:
            raise ValueError(f"站点 {station} 不在线路 {self.line_id} 上")

    def extend_line(self, new_station: str, terminal_station: str):
        """延长线路"""
        if terminal_station not in self.stations:
            raise ValueError(f"终点站 {terminal_station} 不在线路 {self.line_id} 上")
            
        if terminal_station == self.stations[0]:
            self.stations.insert(0, new_station)
        elif terminal_station == self.stations[-1]:
            self.stations.append(new_station)
        else:
            raise ValueError("只能在线路两端延长")
        
        self.reverse_stations = self.stations[::-1] 