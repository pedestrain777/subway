from typing import Dict
from models.station import Station
from models.line import Line

class SubwayEditor:
    def __init__(self, stations: Dict[str, Station], lines: Dict[str, Line]):
        self.stations = stations
        self.lines = lines

    def add_station(self, line_id: str, prev_station: str, next_station: str, 
                   new_station: str, prev_distance: float, next_distance: float):
        """添加新站点"""
        if line_id not in self.lines:
            raise ValueError(f"线路 {line_id} 不存在")
        
        line = self.lines[line_id]
        
        # 验证前后站点是否相邻
        try:
            line.add_station(new_station, prev_station, next_station)
        except ValueError as e:
            raise ValueError(f"无法添加站点：{str(e)}")
        
        # 创建新站点
        new_station_obj = Station(new_station)
        new_station_obj.add_line(line_id)
        self.stations[new_station] = new_station_obj
        
        # 更新相邻站点关系
        new_station_obj.add_adjacent_station(prev_station, prev_distance)
        new_station_obj.add_adjacent_station(next_station, next_distance)
        
        self.stations[prev_station].remove_adjacent_station(next_station)
        self.stations[next_station].remove_adjacent_station(prev_station)
        
        self.stations[prev_station].add_adjacent_station(new_station, prev_distance)
        self.stations[next_station].add_adjacent_station(new_station, next_distance)

    def extend_line(self, line_id: str, terminal_station: str, 
                   new_station: str, distance: float):
        """延长线路"""
        if line_id not in self.lines:
            raise ValueError(f"线路 {line_id} 不存在")
        
        line = self.lines[line_id]
        
        try:
            line.extend_line(new_station, terminal_station)
        except ValueError as e:
            raise ValueError(f"无法延长线路：{str(e)}")
        
        # 创建新站点
        new_station_obj = Station(new_station)
        new_station_obj.add_line(line_id)
        self.stations[new_station] = new_station_obj
        
        # 建立邻接关系
        new_station_obj.add_adjacent_station(terminal_station, distance)
        self.stations[terminal_station].add_adjacent_station(new_station, distance)

    def remove_station(self, station_name: str):
        """删除站点"""
        if station_name not in self.stations:
            raise ValueError(f"站点 {station_name} 不存在")
        
        station = self.stations[station_name]
        adjacent_stations = list(station.adjacent_stations.items())
        
        if len(adjacent_stations) != 2:
            raise ValueError("只能删除恰好有两个相邻站点的车站")
        
        # 获取相邻站点
        prev_station, prev_distance = adjacent_stations[0]
        next_station, next_distance = adjacent_stations[1]
        
        # 计算新的距离（两段距离之和）
        new_distance = prev_distance + next_distance
        
        # 更新相邻站点的连接关系
        self.stations[prev_station].update_adjacent_station(station_name, next_station, new_distance)
        self.stations[next_station].update_adjacent_station(station_name, prev_station, new_distance)
        
        # 从所有包含该站点的线路中删除该站点
        for line_id in station.lines:
            self.lines[line_id].remove_station(station_name)
        
        # 删除站点
        del self.stations[station_name] 