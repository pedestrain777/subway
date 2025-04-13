from typing import Dict, List, Optional
from models.station import Station
from models.line import Line
from services.subway_editor import SubwayEditor
from services.subway_planner import SubwayPlanner
from utils.initializer import initialize_from_json

class SubwaySystemEditor:
    """用于编辑地铁系统的类"""
    
    def __init__(self, subway_system):
        """初始化编辑器
        
        Args:
            subway_system: 要编辑的地铁系统实例
        """
        self.subway_system = subway_system
    
    def extend_line(self, line_id, terminal_station, new_station, distance):
        """延长一条线路
        
        Args:
            line_id: 要延长的线路ID
            terminal_station: 要连接的终点站名称
            new_station: 新站点名称
            distance: 两站点间的距离
            
        Returns:
            更新后的线路对象
        """
        if line_id not in self.subway_system.lines:
            raise ValueError(f"线路 {line_id} 不存在")
        
        line = self.subway_system.lines[line_id]
        
        # 检查终点站是否在该线路上
        if terminal_station not in line.stations:
            raise ValueError(f"站点 {terminal_station} 不在线路 {line_id} 上")
        
        # 检查新站点是否已存在
        if new_station in self.subway_system.stations:
            raise ValueError(f"站点 {new_station} 已存在")
        
        # 创建新站点
        from models.station import Station
        new_station_obj = Station(new_station)
        new_station_obj.add_line(line_id)
        
        # 将新站点添加到系统
        self.subway_system.stations[new_station] = new_station_obj
        
        # 更新线路信息
        terminal_idx = line.stations.index(terminal_station)
        
        # 如果终点站是线路的第一个站点，则将新站点添加到线路的开头
        if terminal_idx == 0:
            line.stations.insert(0, new_station)
        # 否则将新站点添加到线路的末尾
        else:
            line.stations.append(new_station)
        
        # 更新相邻站点信息
        new_station_obj.add_adjacent_station(terminal_station, distance)
        self.subway_system.stations[terminal_station].add_adjacent_station(new_station, distance)
        
        return line

class SubwaySystem:
    def __init__(self, data_file='resources/data/line_speed_final.json'):
        """初始化地铁系统
        
        Args:
            data_file: 包含地铁系统数据的JSON文件路径
        """
        self.data_file = data_file
        self.stations = {}  # 站点名称到Station对象的映射
        self.lines = {}     # 线路名称到Line对象的映射
        self.load_data()
        self.editor = SubwaySystemEditor(self)  # 初始化编辑器

    def load_data(self):
        """从JSON文件加载地铁系统数据"""
        self.stations, self.lines = initialize_from_json(self.data_file)
        # 初始化规划器
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
    
    def get_route_details(self, start: str, end: str, mode: str = "time") -> dict:
        """获取路线详细信息，用于地图显示
        
        Args:
            start: 起点站
            end: 终点站
            mode: 规划模式，"time"为最短时间，"transfers"为最少换乘
            
        Returns:
            dict: 包含路线详细信息的字典
        """
        try:
            if mode == "time":
                path, total_time, lines = self.planner.find_shortest_time_path(start, end)
                if not path:
                    return {"error": "未找到可行路线"}
                
                details = self.planner.calculate_route_details(path, lines)
                
                return {
                    "path": path,
                    "time": total_time,
                    "lines": lines,
                    "transfers": details.get("transfers", 0),
                    "total_distance": details.get("total_distance", 0),
                    "wait_time": details.get("wait_time", 0),
                    "segments": details.get("segments", []),
                    "fare": self.calculate_fare(details.get("total_distance", 0))
                }
            else:
                paths = self.planner.find_least_transfers_path(start, end)
                if not paths:
                    return {"error": "未找到可行路线"}
                
                # 使用第一条路径（最少换乘且时间最短的路径）
                path, transfers, lines, total_time = paths[0]
                details = self.planner.calculate_route_details(path, lines)
                
                return {
                    "path": path,
                    "time": total_time,
                    "lines": lines,
                    "transfers": transfers,
                    "total_distance": details.get("total_distance", 0),
                    "wait_time": details.get("wait_time", 0),
                    "segments": details.get("segments", []),
                    "fare": self.calculate_fare(details.get("total_distance", 0))
                }
                
        except ValueError as e:
            return {"error": str(e)}
            
    def get_all_transfer_routes(self, start: str, end: str) -> list:
        """获取所有最少换乘路线方案
        
        Args:
            start: 起点站
            end: 终点站
            
        Returns:
            list: 包含所有最少换乘路线方案的列表
        """
        try:
            paths = self.planner.find_least_transfers_path(start, end)
            if not paths:
                return []
                
            result = []
            for path, transfers, lines, total_time in paths:
                details = self.planner.calculate_route_details(path, lines)
                
                result.append({
                    "path": path,
                    "time": total_time,
                    "lines": lines,
                    "transfers": transfers,
                    "total_distance": details.get("total_distance", 0),
                    "wait_time": details.get("wait_time", 0),
                    "segments": details.get("segments", []),
                    "fare": self.calculate_fare(details.get("total_distance", 0))
                })
            
            # 按时间排序
            result.sort(key=lambda x: x["time"])
            
            return result
        except ValueError as e:
            print(f"获取所有最少换乘路线失败: {str(e)}")
            return []
            
    def add_custom_station(self, station_name: str, line_id: str, connected_station: str, distance: float) -> bool:
        """添加自定义站点到地铁系统
        
        Args:
            station_name: 新站点的名称
            line_id: 新站点所属的线路ID
            connected_station: 与新站点相连的已有站点名称
            distance: 新站点与相连站点的距离（米）
            
        Returns:
            bool: 是否成功添加站点
        """
        try:
            # 检查线路是否存在
            if line_id not in self.lines:
                raise ValueError(f"线路 {line_id} 不存在")
                
            # 检查连接站点是否存在并且在指定线路上
            if connected_station not in self.stations:
                raise ValueError(f"站点 {connected_station} 不存在")
                
            if line_id not in self.stations[connected_station].lines:
                raise ValueError(f"站点 {connected_station} 不在线路 {line_id} 上")
                
            # 检查新站点名称是否已存在
            if station_name in self.stations:
                raise ValueError(f"站点 {station_name} 已存在")
                
            # 创建新站点
            new_station = Station(station_name)
            new_station.add_line(line_id)
            
            # 获取线路对象
            line = self.lines[line_id]
            
            # 确定新站点在线路中的位置
            connected_idx = line.stations.index(connected_station)
            
            # 将新站点添加到线路
            if connected_idx == 0:
                # 如果连接站是线路的第一个站点，则在开头添加新站点
                line.stations.insert(0, station_name)
            elif connected_idx == len(line.stations) - 1:
                # 如果连接站是线路的最后一个站点，则在末尾添加新站点
                line.stations.append(station_name)
            else:
                # 如果连接站在中间，则需要用户指定方向，默认添加到后面
                line.stations.insert(connected_idx + 1, station_name)
            
            # 更新站点间的连接关系
            new_station.add_adjacent_station(connected_station, distance)
            self.stations[connected_station].add_adjacent_station(station_name, distance)
            
            # 将新站点添加到系统
            self.stations[station_name] = new_station
            
            # 更新规划器
            self.planner = SubwayPlanner(self.stations, self.lines)
            
            return True
            
        except ValueError as e:
            print(f"添加自定义站点失败: {str(e)}")
            return False 