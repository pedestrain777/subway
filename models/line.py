from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class Line:
    line_id: str  # 线路编号
    start_times: Dict[str, Dict[str, str]]  # 不同始发站的发车时间 {station_name: {time_id: time}}
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

    def add_start_time(self, station: str, time_id: str, time: str):
        """添加站点的发车时间
        
        Args:
            station: 站点名称
            time_id: 发车时间编号
            time: 发车时间（格式：HH:MM）
        """
        if station not in self.start_times:
            self.start_times[station] = {}
        self.start_times[station][time_id] = time
        
    def get_start_times(self, station: str) -> Dict[str, str]:
        """获取指定站点的所有发车时间
        
        Args:
            station: 站点名称
            
        Returns:
            Dict[str, str]: 发车时间字典 {time_id: time}，如果站点不存在则返回空字典
        """
        return self.start_times.get(station, {})
        
    def get_all_start_times(self) -> Dict[str, Dict[str, str]]:
        """获取所有站点的发车时间
        
        Returns:
            Dict[str, Dict[str, str]]: 所有站点的发车时间字典
        """
        return self.start_times.copy()

    def get_earliest_start_time(self, station: str) -> Optional[str]:
        """获取指定站点的最早发车时间
        
        Args:
            station: 站点名称
            
        Returns:
            Optional[str]: 最早发车时间，如果站点不存在则返回None
        """
        if station in self.start_times and self.start_times[station]:
            return min(self.start_times[station].values())
        return None

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