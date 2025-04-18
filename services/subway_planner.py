from typing import List, Dict, Tuple, Set
import heapq
from models.station import Station
from models.line import Line
import json
import networkx as nx
from collections import deque
import random

class SubwayPlanner:
    def __init__(self, stations: Dict[str, Station] = None, lines: Dict[str, Line] = None):
        """初始化地铁规划器
        
        Args:
            stations: 站点字典，如果为None则创建空字典
            lines: 线路字典，如果为None则创建空字典
        """
        self.stations = stations if stations is not None else {}
        self.lines = lines if lines is not None else {}
        self.graph = nx.Graph()  # 使用NetworkX的图结构
        
        # 如果传入了stations和lines，则加载发车时间
        if stations is not None and lines is not None:
            self.load_departure_times(self.lines)
        
        # 构建图
        self.build_graph()
        
        # 用于存储每条路线的等待时间
        self.route_wait_times = {}

    def _add_circle_line_connections(self):
        """为环形线路添加首尾站点的连接"""
        for line_id in self.circle_lines:
            line = self.lines[line_id]
            if len(line.stations) >= 2:
                first_station = line.stations[0]
                last_station = line.stations[-1]
                
                # 在两个方向都添加连接
                if first_station in self.stations and last_station in self.stations:
                    # 使用实际距离数据
                    distance = {
                        "2号线": 1810,  # 西直门到积水潭的实际距离
                        "10号线": 1441  # 火器营到巴沟的实际距离
                    }[line_id]
                    
                    self.stations[first_station].add_adjacent_station(last_station, distance)
                    self.stations[last_station].add_adjacent_station(first_station, distance)

    def calculate_travel_time(self, distance: float, speed: float) -> float:
        """计算行驶时间（分钟）"""
        return (distance / 1000) / (speed / 60)

    def get_line_between_stations(self, station1: str, station2: str, current_line: str = None) -> Set[str]:
        """获取连接两个站点的所有线路
        
        Args:
            station1: 第一个站点名称
            station2: 第二个站点名称
            current_line: 当前正在使用的线路（如果有）
            
        Returns:
            Set[str]: 两站点之间的所有共同线路，如果没有共同线路则返回空集合
        """
        common_lines = self.stations[station1].lines & self.stations[station2].lines
        
        if not common_lines:
            return set()
        
        # 如果指定了当前线路，并且该线路是共同线路之一，则将其放在集合的第一位
        if current_line and current_line in common_lines:
            return common_lines
            
        return common_lines

    def load_lines(self):
        pass

    def find_least_transfers_path(self, start: str, end: str) -> List[Tuple[List[str], int, List[str], float]]:
        """查找最少换乘路径，返回所有最短换乘路径并按时间排序
        
        Returns:
            List[Tuple[path, transfers, lines, time]]: 所有最短换乘路径，按时间排序
        """
        # 特殊处理：西二旗和清河站之间的换乘
        if (start in ["西二旗", "清河站"] and end in ["西二旗", "清河站"]):
            # 获取两站之间的距离
            distance = self.stations[start].adjacent_stations[end]
            
            # 返回两条线路的方案
            path = [start, end]
            path_details = []
            
            # 13号线方案
            line_13_speed = self.lines["13号线"].speed
            time_13 = self.calculate_travel_time(distance, line_13_speed)
            path_details.append((path, 0, ["13号线"], time_13))
            
            # 昌平线方案
            line_cp_speed = self.lines["昌平线"].speed
            time_cp = self.calculate_travel_time(distance, line_cp_speed)
            path_details.append((path, 0, ["昌平线"], time_cp))
            
            # 按时间从短到长排序
            path_details.sort(key=lambda x: x[3])
            return path_details
            
        # 特殊处理：环球度假区和花庄之间的换乘
        if (start in ["环球度假区", "花庄"] and end in ["环球度假区", "花庄"]):
            # 获取两站之间的距离
            distance = self.stations[start].adjacent_stations[end]
            
            # 返回两条线路的方案
            path = [start, end]
            path_details = []
            
            # 1号线/八通线方案
            line_1_speed = self.lines["1号线/八通线"].speed
            time_1 = self.calculate_travel_time(distance, line_1_speed)
            path_details.append((path, 0, ["1号线/八通线"], time_1))
            
            # 7号线方案
            line_7_speed = self.lines["7号线"].speed
            time_7 = self.calculate_travel_time(distance, line_7_speed)
            path_details.append((path, 0, ["7号线"], time_7))
            
            # 按时间从短到长排序
            path_details.sort(key=lambda x: x[3])
            return path_details
            
        if start not in self.stations or end not in self.stations:
            raise ValueError("起点或终点站不存在")
            
        all_paths = []
        min_transfers_found = float('inf')
        
        def dfs(current: str, path: List[str], lines_used: List[str], transfers: int, visited_stations: Set[str], visited_edges: Set[Tuple[str, str]], current_line: str = None):
            """深度优先搜索
            Args:
                current: 当前站点
                path: 当前路径
                lines_used: 当前使用的线路
                transfers: 当前换乘次数
                visited_stations: 已访问的站点
                visited_edges: 已访问的边（站点对）
                current_line: 当前使用的线路
            """
            nonlocal min_transfers_found
            
            # 如果当前换乘次数已经超过已知的最少换乘次数，剪枝
            if transfers > min_transfers_found:
                return
                
            if current == end:
                if transfers < min_transfers_found:
                    min_transfers_found = transfers
                    all_paths.clear()  # 清空之前的路径
                if transfers == min_transfers_found:
                    all_paths.append((path.copy(), transfers, lines_used.copy()))
                return
            
            current_station = self.stations[current]
            
            # 获取所有可能的下一站
            for next_station in current_station.adjacent_stations:
                # 避免重复访问同一个站点
                if next_station in visited_stations:
                    continue
                    
                # 创建边标识（按字母顺序排序以确保唯一性）
                edge = tuple(sorted([current, next_station]))
                
                # 避免重复使用同一条边
                if edge in visited_edges:
                    continue
                    
                # 获取到下一站的所有可能线路
                next_lines = self.get_line_between_stations(current, next_station)
                
                if not next_lines:
                    continue
                
                # 创建新的集合，避免修改原始集合
                new_visited_stations = set(visited_stations)
                new_visited_edges = set(visited_edges)
                new_visited_stations.add(next_station)
                new_visited_edges.add(edge)
                
                path.append(next_station)
                
                # 对每条可能的线路都进行尝试
                for next_line in next_lines:
                    # 计算是否需要换乘
                    new_transfers = transfers
                    if current_line and next_line != current_line:
                        new_transfers += 1
                        # 如果换乘次数已经超过已知的最少换乘次数，剪枝
                        if new_transfers > min_transfers_found:
                            continue
                    
                    # 添加当前使用的线路
                    lines_used.append(next_line)
                    
                    dfs(next_station, path, lines_used, new_transfers, new_visited_stations, new_visited_edges, next_line)
                    
                    # 回溯时移除当前使用的线路
                    lines_used.pop()
                
                path.pop()
 
        # 开始搜索
        initial_visited_stations = {start}
        initial_visited_edges = set()
        dfs(start, [start], [], 0, initial_visited_stations, initial_visited_edges, None)
 
        if not all_paths:
            return None
 
        # 计算每条路径的详细信息
        path_details = []
        for path, transfers, lines_used in all_paths:
            # 计算总时间
            total_time = 0
            for i in range(len(path)-1):
                current = path[i]
                next_station = path[i+1]
                distance = self.stations[current].adjacent_stations[next_station]
                line = lines_used[i]  # 使用DFS中记录的线路
                
                # 计算行驶时间
                travel_time = self.calculate_travel_time(distance, self.lines[line].speed)
                total_time += travel_time
                
                # 添加停站时间（除终点站外每站1分钟）
                if i < len(path)-2:
                    total_time += 1
                
                # 如果需要换乘，添加换乘时间
                if i > 0 and lines_used[i-1] != line:
                    total_time += 5
            
            path_details.append((path, transfers, lines_used, total_time))
 
        # 按时间排序
        path_details.sort(key=lambda x: x[3])
                
        return path_details
    
    def build_graph(self):
        # 实现构建图的逻辑
        pass

    def find_shortest_time_path(self, start: str, end: str) -> Tuple[List[str], float, List[str]]:
        """查找最短时间路径
        
        直接从最少换乘路径中选择时间最短的路径
        """
        if start not in self.stations or end not in self.stations:
            raise ValueError("起点或终点站不存在")
            
        # 获取所有最少换乘路径
        path_details = self.find_least_transfers_path(start, end)
        
        if not path_details:
            return None, None, None
            
        # find_least_transfers_path已经按时间排序，直接取第一条就是时间最短的
        path, transfers, lines, total_time = path_details[0]
        
        # 生成起点-终点的唯一标识
        route_key = f"{start}-{end}"
        
        # 添加随机等车时间，并实现递减逻辑
        if route_key not in self.route_wait_times:
            # 第一次查询这条路线，生成0到4分钟的随机等待时间
            self.route_wait_times[route_key] = random.uniform(0, 4)
        else:
            # 后续查询，等待时间递减（但不低于0）
            self.route_wait_times[route_key] = max(0, self.route_wait_times[route_key] * 0.8)
        
        # 将等待时间加到总时间上
        wait_time = self.route_wait_times[route_key]
        total_time += wait_time
        
        return path, total_time, lines

    def calculate_route_details(self, path: List[str], lines: List[str] = None) -> Dict:
        """计算路径的详细信息"""
        details = {
            "total_distance": 0,
            "total_time": 0,
            "transfers": 0,
            "segments": [],
            "wait_time": 0  # 添加等车时间字段
        }
        
        if len(path) <= 1:
            return details
            
        # 如果没有提供线路信息，需要重新计算
        if not lines:
            lines = self._optimize_path_lines(path)
            
        current_line = None
        
        # 计算等车时间
        route_key = f"{path[0]}-{path[-1]}"
        if route_key in self.route_wait_times:
            details["wait_time"] = self.route_wait_times[route_key]
            details["total_time"] += details["wait_time"]  # 将等车时间加入总时间
        
        for i in range(len(path)-1):
            current = path[i]
            next_station = path[i+1]
            
            # 获取距离
            distance = self.stations[current].adjacent_stations[next_station]
            details["total_distance"] += distance
            
            # 如果提供了线路信息，使用它
            if lines and i < len(lines):
                line = lines[i]
            else:
                # 否则获取连接线路
                line_set = self.get_line_between_stations(current, next_station)
                if current_line and current_line in line_set:
                    line = current_line  # 优先使用当前线路
                else:
                    line = next(iter(line_set))  # 使用第一条线路
            
            # 计算换乘次数
            if current_line and line != current_line:
                details["transfers"] += 1
            current_line = line
            
            # 计算时间
            travel_time = self.calculate_travel_time(distance, self.lines[line].speed)
            
            segment = {
                "from": current,
                "to": next_station,
                "line": line,
                "distance": distance,
                "time": travel_time
            }
            
            details["total_time"] += travel_time
            
            # 每个站点停留时间（1分钟），终点站不计
            if i < len(path) - 2:
                details["total_time"] += 1
                
            # 换乘时间（5分钟）
            if i > 0 and lines[i-1] != line:
                details["total_time"] += 5
                
            details["segments"].append(segment)
            
        return details

    def load_stations(self):
        # 实现加载站点的逻辑
        pass

    def load_departure_times(self, lines: Dict[str, Line]):
        """从JSON文件加载发车时间数据"""
        try:
            with open('resources/data/parsed_departure_times.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 使用工作日数据
            weekday_data = data.get('weekday', {})
            
            for line_id, line_data in weekday_data.items():
                if line_id in lines:
                    line = lines[line_id]
                    
                    # 处理正向和反向的发车时间
                    for direction, stations in line_data.items():
                        for station, times in stations.items():
                            for time_id, time in times.items():
                                line.add_start_time(station, time_id, time)  # 添加time参数
                                
        except Exception as e:
            print(f"加载发车时间数据失败: {str(e)}")
            raise

   
