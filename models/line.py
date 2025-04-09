from typing import List, Dict
from dataclasses import dataclass

"""地铁线路类，管理单条线路的基本信息和站点序列"""

@dataclass
class Line:
    line_id: str  # 线路编号
    start_times: Dict[str, str]  # 不同始发站的发车时间 {station_name: time}
    speed: float  # 线路速度（km/h）
    stations: List[str]  # 正向站点列表
    reverse_stations: List[str]  # 反向站点列表
    
    def __init__(self, line_id: str, speed: float):
        """初始化线路，设置ID和运行速度"""
        self.line_id = line_id
        self.speed = speed
        self.start_times = {}  # 首班车时间
        self.stations = []     # 正向站点列表
        self.reverse_stations = []  # 反向站点列表

    def add_start_time(self, station: str, time: str):
        """添加始发站的首班车时间"""
        self.start_times[station] = time

    def set_stations(self, stations: List[str]):
        """设置线路的站点序列，自动生成反向序列"""
        self.stations = stations
        self.reverse_stations = stations[::-1]

    def add_station(self, new_station: str, prev_station: str, next_station: str):
        """在两个相邻站点之间插入新站点"""
        if prev_station not in self.stations or next_station not in self.stations:
            raise ValueError("前后站点必须在当前线路中")
        
        prev_idx = self.stations.index(prev_station)
        next_idx = self.stations.index(next_station)
        if abs(prev_idx - next_idx) != 1:
            raise ValueError("指定的站点不相邻")
        
        insert_idx = max(prev_idx, next_idx)
        self.stations.insert(insert_idx, new_station)
        self.reverse_stations = self.stations[::-1]

    def remove_station(self, station: str):
        """从线路中移除指定站点"""
        if station in self.stations:
            self.stations.remove(station)  # list.remove(): 删除列表中第一个匹配的元素
            self.reverse_stations = self.stations[::-1]  # [::-1]: 列表切片，创建反向副本

    def extend_line(self, new_station: str, terminal_station: str):
        """在线路终点站延长线路"""
        if terminal_station not in [self.stations[0], self.stations[-1]]:
            raise ValueError("只能在终点站延长线路")
        
        if terminal_station == self.stations[0]:
            self.stations.insert(0, new_station)
        else:
            self.stations.append(new_station)
        
        self.reverse_stations = self.stations[::-1] 