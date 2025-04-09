from typing import Dict
from models.station import Station
from models.line import Line

"""地铁网络编辑器，提供站点和线路的增删改功能"""

class SubwayEditor:
    def __init__(self, stations: Dict[str, Station], lines: Dict[str, Line]):
        """初始化编辑器，管理站点和线路集合"""
        self.stations = stations
        self.lines = lines

    def add_station(self, line_id: str, prev_station: str, next_station: str, 
                   new_station: str, prev_distance: float, next_distance: float):
        """在指定线路上添加新站点"""
        if line_id not in self.lines:
            raise ValueError(f"线路 {line_id} 不存在")
        
        line = self.lines[line_id]
        
        try:
            line.add_station(new_station, prev_station, next_station)
        except ValueError as e:
            raise ValueError(f"无法添加站点：{str(e)}")
        
        new_station_obj = Station(new_station)
        new_station_obj.add_line(line_id)
        self.stations[new_station] = new_station_obj
        
        new_station_obj.add_adjacent_station(prev_station, prev_distance)
        new_station_obj.add_adjacent_station(next_station, next_distance)
        
        self.stations[prev_station].remove_adjacent_station(next_station)
        self.stations[next_station].remove_adjacent_station(prev_station)
        
        self.stations[prev_station].add_adjacent_station(new_station, prev_distance)
        self.stations[next_station].add_adjacent_station(new_station, next_distance)

    def extend_line(self, line_id: str, terminal_station: str, 
                   new_station: str, distance: float):
        """延长指定线路"""
        if line_id not in self.lines:
            raise ValueError(f"线路 {line_id} 不存在")
        
        line = self.lines[line_id]
        
        try:
            line.extend_line(new_station, terminal_station)
        except ValueError as e:
            raise ValueError(f"无法延长线路：{str(e)}")
        
        new_station_obj = Station(new_station)
        new_station_obj.add_line(line_id)
        self.stations[new_station] = new_station_obj
        
        new_station_obj.add_adjacent_station(terminal_station, distance)
        self.stations[terminal_station].add_adjacent_station(new_station, distance)

    def remove_station(self, station_name: str):
        """删除指定站点并维护相关连接"""
        if station_name not in self.stations:
            raise ValueError(f"站点 {station_name} 不存在")
        
        station = self.stations[station_name]
        adjacent_stations = list(station.adjacent_stations.items())  # dict.items(): 返回字典的键值对列表
        
        if len(adjacent_stations) != 2:
            raise ValueError("只能删除恰好有两个相邻站点的车站")
        
        prev_station, prev_distance = adjacent_stations[0]
        next_station, next_distance = adjacent_stations[1]
        
        new_distance = prev_distance + next_distance
        
        self.stations[prev_station].update_adjacent_station(station_name, next_station, new_distance)
        self.stations[next_station].update_adjacent_station(station_name, prev_station, new_distance)
        
        for line_id in station.lines:
            self.lines[line_id].remove_station(station_name)
        
        del self.stations[station_name]  # del: 删除字典中指定的键值对 