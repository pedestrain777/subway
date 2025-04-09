from typing import List, Dict, Tuple, Set
import heapq
from models.station import Station
from models.line import Line

class SubwayPlanner:
    def __init__(self, stations: Dict[str, Station], lines: Dict[str, Line]):
        self.stations = stations
        self.lines = lines
        # 添加环形线路的特殊处理
        self.circle_lines = {"2号线", "10号线"}  # 添加2号线作为环形线路
        self._add_circle_line_connections()

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

    def get_line_between_stations(self, station1: str, station2: str, current_line: str = None) -> str:
        """获取连接两个站点的线路，优先返回当前线路"""
        common_lines = self.stations[station1].lines & self.stations[station2].lines
        if not common_lines:
            return None
        
        if current_line and current_line in common_lines:
            return current_line
            
        return next(iter(common_lines))

    def find_least_transfers_path(self, start: str, end: str) -> Tuple[List[str], int, List[str]]:
        """查找最少换乘路径，当有多条最少换乘路径时选择时间最短的"""
        if start not in self.stations or end not in self.stations:
            raise ValueError("起点或终点站不存在")

        all_paths = []
        min_transfers_found = float('inf')  # 记录已找到的最少换乘次数
        
        def dfs(current: str, path: List[str], transfers: int, visited_edges: Set[Tuple[str, str]]):
            """深度优先搜索
            Args:
                current: 当前站点
                path: 当前路径
                transfers: 当前换乘次数
                visited_edges: 已访问的边（站点对）
            """
            nonlocal min_transfers_found
            
            if transfers >= min_transfers_found:
                return
            
            if current == end:
                min_transfers_found = transfers
                all_paths.append(path.copy())
                return
            
            current_station = self.stations[current]
            last_station = path[-2] if len(path) >= 2 else None
            
            # 获取当前线路（如果有）
            current_line = None
            if last_station:
                current_line = self.get_line_between_stations(last_station, current)

            # 获取所有可能的下一站
            for next_station in current_station.adjacent_stations:
                # 创建边标识（按字母顺序排序以确保唯一性）
                edge = tuple(sorted([current, next_station]))
                
                # 避免重复使用同一条边
                if edge in visited_edges:
                    continue
                    
                # 获取到下一站的线路
                next_line = self.get_line_between_stations(current, next_station)
                
                # 计算是否需要换乘
                new_transfers = transfers
                if current_line and next_line != current_line:
                    new_transfers += 1
                    if new_transfers >= min_transfers_found:
                        continue
                
                path.append(next_station)
                visited_edges.add(edge)
                dfs(next_station, path, new_transfers, visited_edges)
                visited_edges.remove(edge)
                path.pop()

        # 开始搜索
        dfs(start, [start], 0, set())

        if not all_paths:
            return None, None, None

        # 计算每条路径的换乘次数和时间
        path_details = []
        for path in all_paths:
            transfers = self._count_transfers(path)
            # 计算总时间
            total_time = 0
            for i in range(len(path)-1):
                current = path[i]
                next_station = path[i+1]
                distance = self.stations[current].adjacent_stations[next_station]
                line = self.get_line_between_stations(current, next_station)
                # 计算行驶时间
                travel_time = self.calculate_travel_time(distance, self.lines[line].speed)
                total_time += travel_time
                # 添加停站时间（除终点站外每站1分钟）
                if i < len(path)-2:
                    total_time += 1
                # 如果需要换乘，添加换乘时间
                if i > 0:
                    prev_line = self.get_line_between_stations(path[i-1], current)
                    if prev_line != line:
                        total_time += 5
            
            path_details.append((path, transfers, total_time))

        # 找出换乘次数最少的路径
        min_transfers = min(details[1] for details in path_details)
        min_transfer_paths = [details for details in path_details if details[1] == min_transfers]
        
        # 在换乘次数相同的路径中选择时间最短的
        best_path, transfers, _ = min(min_transfer_paths, key=lambda x: x[2])
        lines = self._get_path_lines(best_path)

        return best_path, transfers, lines

    def _count_transfers(self, path: List[str]) -> int:
        """计算给定路径的换乘次数"""
        transfers = 0
        current_line = None
        for i in range(len(path)-1):
            # 获取连接相邻站点的线路
            line = self.get_line_between_stations(path[i], path[i+1])
            # 如果与当前线路不同，需要换乘
            if current_line and line != current_line:
                transfers += 1
            current_line = line
        return transfers

    def _get_path_lines(self, path: List[str]) -> List[str]:
        """获取路径经过的线路列表"""
        lines = []
        current_line = None
        for i in range(len(path)-1):
            line = self.get_line_between_stations(path[i], path[i+1])
            # 只在换乘时添加新线路
            if line != current_line:
                lines.append(line)
                current_line = line
        return lines

    def find_shortest_time_path(self, start: str, end: str) -> Tuple[List[str], float, List[str]]:
        """查找最短时间路径"""
        if start not in self.stations or end not in self.stations:
            raise ValueError("起点或终点站不存在")

        # 初始化数据
        times = {station: float('inf') for station in self.stations}
        times[start] = 0
        previous = {station: None for station in self.stations}
        lines_used = {station: None for station in self.stations}
        visited = set()
        
        # 优先队列：(总时间, 当前线路, 站点)
        pq = [(0, None, start)]
        
        while pq:
            current_time, current_line, current = heapq.heappop(pq)
            
            if current in visited:
                continue
                
            visited.add(current)
            
            if current == end:
                break
                
            current_station = self.stations[current]
            
            # 检查所有相邻站点
            for next_station, distance in current_station.adjacent_stations.items():
                if next_station in visited:
                    continue
                    
                # 获取连接线路，优先使用当前线路
                line = self.get_line_between_stations(current, next_station, current_line)
                if not line:
                    continue
                    
                # 计算时间
                travel_time = self.calculate_travel_time(distance, self.lines[line].speed)
                # 添加停站时间
                travel_time += 1
                # 如果需要换乘，添加换乘时间
                if current_line and line != current_line:
                    travel_time += 5
                
                new_time = current_time + travel_time
                
                if new_time < times[next_station]:
                    times[next_station] = new_time
                    previous[next_station] = current
                    lines_used[next_station] = line
                    heapq.heappush(pq, (new_time, line, next_station))
        
        # 构建路径
        if times[end] == float('inf'):
            return None, None, None
            
        path = []
        current = end
        path_lines = []
        
        while current:
            path.append(current)
            if lines_used[current]:
                path_lines.append(lines_used[current])
            current = previous[current]
            
        return path[::-1], times[end], list(dict.fromkeys(path_lines[::-1]))

    def calculate_route_details(self, path: List[str], lines: List[str]) -> Dict:
        """计算路线详细信息"""
        details = {
            "total_distance": 0,
            "total_time": 0,
            "transfers": 0,
            "segments": []
        }
        
        current_line = None
        for i in range(len(path) - 1):
            current = path[i]
            next_station = path[i + 1]
            
            # 获取距离
            distance = self.stations[current].adjacent_stations[next_station]
            # 获取线路，优先使用当前线路
            line = self.get_line_between_stations(current, next_station, current_line)
            
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
            
            details["segments"].append(segment)
            details["total_distance"] += distance
            details["total_time"] += travel_time
        
        # 添加停站时间（除始发站外每站1分钟）
        details["total_time"] += len(path) - 1
        # 添加换乘时间（每次换乘5分钟）
        details["total_time"] += details["transfers"] * 5
        
        return details 

if __name__ == "__main__":
    import sys
    import os
    # 添加项目根目录到 Python 路径
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from utils.initializer import initialize_from_json
    
    # 初始化地铁系统
    stations, lines = initialize_from_json('resources/data/line_speed_final.json')
    planner = SubwayPlanner(stations, lines)
    
    # 测试八里桥到天宫院的路径
    start = "八里桥"
    end = "天宫院"
    path, transfers, lines = planner.find_least_transfers_path(start, end) 