from typing import Dict, List, Optional
from models.station import Station
from models.line import Line
from services.subway_editor import SubwayEditor
from services.subway_planner import SubwayPlanner
from utils.initializer import initialize_from_json

class SubwaySystem:
    def __init__(self):
        # 保存原始数据的副本，用于重置
        self.stations, self.lines = initialize_from_json('resources/data/line_speed_final.json')
        self.editor = SubwayEditor(self.stations, self.lines)
        self.planner = SubwayPlanner(self.stations, self.lines)

    def get_system_data(self):
        """获取当前系统数据，用于前端显示"""
        data = {}
        for line_id, line in self.lines.items():
            data[line_id] = {
                'speed': line.speed,
                'stations': line.stations
            }
        return data

    def get_departure_times(self, line_id: str) -> Dict[str, str]:
        """获取指定线路所有站点的发车时间
        
        Args:
            line_id: 线路ID
            
        Returns:
            Dict[str, str]: 所有站点的发车时间字典，如果线路不存在则返回空字典
        """
        if line_id in self.lines:
            return self.lines[line_id].get_all_start_times()
        return {}
        
    def get_station_departure_time(self, line_id: str, station: str) -> Optional[str]:
        """获取指定线路指定站点的发车时间
        
        Args:
            line_id: 线路ID
            station: 站点名称
            
        Returns:
            Optional[str]: 发车时间字符串，如果线路或站点不存在则返回None
        """
        if line_id in self.lines:
            return self.lines[line_id].get_start_time(station)
        return None

    def calculate_fare(self, distance: float) -> float:
        """计算票价"""
        if distance <= 6000:  # 6公里以内
            return 3
        elif distance <= 12000:  # 6-12公里
            return 4
        elif distance <= 22000:  # 12-22公里
            return 5
        elif distance <= 32000:  # 22-32公里
            return 6
        else:  # 32公里以上
            return 7 + ((distance - 32000) // 20000)  # 每增加20公里增加1元

    def format_route(self, path: List[str], total_time: float, lines: List[str], details: Dict) -> str:
        """格式化路线信息"""
        result = []
        result.append(f"=== 乘车方案 ===")
        result.append(f"起点: {path[0]}")
        result.append(f"终点: {path[-1]}")
        result.append(f"总距离: {details['total_distance']/1000:.2f}公里")
        result.append(f"总时间: {total_time:.2f}分钟")
        result.append(f"换乘次数: {details['transfers']}")
        result.append(f"票价: {self.calculate_fare(details['total_distance'])}元")
        
        result.append("\n详细路线:")
        current_line = None
        for segment in details['segments']:
            if segment['line'] != current_line:
                current_line = segment['line']
                result.append(f"\n乘坐 {current_line}")
            result.append(f"{segment['from']} -> {segment['to']}")
            
        result.append("\n" + "="*30 + "\n")  # 添加分隔线
        return "\n".join(result)

    def plan_route(self, start: str, end: str, mode: str = "time") -> str:
        """规划路线"""
        try:
            if mode == "time":
                path, total_time, lines = self.planner.find_shortest_time_path(start, end)
                if not path:
                    return "未找到可行路线"
                details = self.planner.calculate_route_details(path, lines)
                return self.format_route(path, total_time, lines, details)
            else:
                paths = self.planner.find_least_transfers_path(start, end)
                if not paths:
                    return "未找到可行路线"
                
                result = []
                result.append("最少换乘路线方案：\n")
                
                # 遍历所有路径并格式化显示
                for i, (path, transfers, lines, total_time) in enumerate(paths, 1):
                    result.append(f"\n{'='*15} 路线 {i} {'='*15}")
                    details = self.planner.calculate_route_details(path, lines)
                    result.append(self.format_route(path, total_time, lines, details))
                
                return "\n".join(result)
                
        except ValueError as e:
            return f"错误：{str(e)}" 