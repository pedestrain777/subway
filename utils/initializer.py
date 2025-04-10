import json
from typing import Dict, Tuple
from models.station import Station
from models.line import Line
import os

def initialize_from_json(line_speed_file: str) -> Tuple[Dict[str, Station], Dict[str, Line]]:
    """从JSON文件初始化地铁系统"""
    # 读取线路速度数据
    with open(line_speed_file, 'r', encoding='utf-8') as f:
        line_speeds = json.load(f)
    
    # 读取站点距离数据
    with open('resources/data/station_distance_final.json', 'r', encoding='utf-8') as f:
        station_distances = json.load(f)
        
    # 读取地铁线路数据
    with open('resources/data/subway_lines_final.json', 'r', encoding='utf-8') as f:
        subway_lines = json.load(f)
        
    stations = {}  # 存储所有站点
    lines = {}     # 存储所有线路
    
    # 初始化线路
    for line_id, line_info in line_speeds.items():
        lines[line_id] = Line(line_id, line_info['speed'])
    
    # 初始化站点和连接关系
    for line_data in subway_lines:  # subway_lines是列表，但每个元素是字符串
        # 从station_distances中获取该线路的所有站点对
        line_distances = station_distances.get(line_data, {})
        if not line_distances or line_data not in lines:
            continue
            
        line = lines[line_data]
        station_list = []
        
        # 从站点距离数据中构建站点列表
        for station_pair in line_distances:
            start_station = station_pair['startStation']
            end_station = station_pair['endStation']
            distance = station_pair['distance']
            
            # 添加站点到列表
            if not station_list:
                station_list.append(start_station)
            station_list.append(end_station)
            
            # 创建或更新站点对象
            for station_name in [start_station, end_station]:
                if station_name not in stations:
                    stations[station_name] = Station(station_name)
                stations[station_name].lines.add(line_data)
            
            # 添加相邻站点关系
            stations[start_station].add_adjacent_station(end_station, distance)
            stations[end_station].add_adjacent_station(start_station, distance)
        
        # 设置线路的站点列表
        line.stations = station_list
        
        # 特殊处理13号线，跳过第一个大钟寺站点
        if line_data == "13号线":
            if "大钟寺" in line.stations and line.stations.index("大钟寺") == 0:
                line.stations = line.stations[1:]
    
    # 加载发车时间数据
    load_departure_times(lines)
    
    return stations, lines

def load_departure_times(lines: Dict[str, Line]) -> None:
    """加载发车时间数据到相应的Line对象中
    
    Args:
        lines: 包含所有线路对象的字典
    """
    try:
        # 检查发车时间数据文件是否存在
        departure_times_file = 'resources/data/parsed_departure_times.json'
        if not os.path.exists(departure_times_file):
            print(f"警告: 发车时间数据文件 {departure_times_file} 不存在")
            return
        
        # 读取发车时间数据
        with open(departure_times_file, 'r', encoding='utf-8') as f:
            departure_data = json.load(f)
        
        # 只解析工作日数据作为每天的发车时间
        weekday_key = "工作日"
        if weekday_key in departure_data:
            weekday_data = departure_data[weekday_key]
            
            # 遍历所有线路
            for line_id, line_obj in lines.items():
                if line_id in weekday_data:
                    line_data = weekday_data[line_id]
                    
                    # 遍历所有方向
                    for direction, stations_data in line_data.items():
                        # 遍历所有始发站
                        for station_name, departure_times in stations_data.items():
                            # 保存所有发车时间
                            for time_id, time_value in departure_times.items():
                                line_obj.add_start_time(station_name, time_id, time_value)
        
        print("发车时间数据加载完成")
    except Exception as e:
        print(f"加载发车时间数据时出错: {str(e)}")