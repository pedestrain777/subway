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

    def find_least_transfers_path(self, start: str, end: str) -> List[Tuple[List[str], int, List[str], float]]:
        """查找最少换乘路径，返回所有最短换乘路径并按时间排序
        Returns:
            List[Tuple[path, transfers, lines, time]]: 所有最短换乘路径，按时间排序
        """
        if start not in self.stations or end not in self.stations:
            raise ValueError("起点或终点站不存在")

        all_paths = []
        min_transfers_found = float('inf')
        
        def dfs(current: str, path: List[str], transfers: int, visited_stations: Set[str], visited_edges: Set[Tuple[str, str]], current_line: str = None):
            """深度优先搜索
            Args:
                current: 当前站点
                path: 当前路径
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
                    all_paths.append((path.copy(), current_line))
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
                    
                    dfs(next_station, path, new_transfers, new_visited_stations, new_visited_edges, next_line)
                
                path.pop()

        # 开始搜索
        initial_visited_stations = {start}
        initial_visited_edges = set()
        dfs(start, [start], 0, initial_visited_stations, initial_visited_edges, None)

        if not all_paths:
            return None

        # 计算每条路径的详细信息
        path_details = []
        for path, final_line in all_paths:
            # 重新计算路径中每段的线路选择，选择最优线路（尽量减少换乘）
            optimized_lines = self._optimize_path_lines(path)
            transfers = len(optimized_lines) - 1  # 线路数量减1就是换乘次数
            
            # 计算总时间
            total_time = 0
            for i in range(len(path)-1):
                current = path[i]
                next_station = path[i+1]
                distance = self.stations[current].adjacent_stations[next_station]
                line = optimized_lines[i]  # 使用优化后的线路
                
                # 计算行驶时间
                travel_time = self.calculate_travel_time(distance, self.lines[line].speed)
                total_time += travel_time
                
                # 添加停站时间（除终点站外每站1分钟）
                if i < len(path)-2:
                    total_time += 1
                
                # 如果需要换乘，添加换乘时间
                if i > 0 and optimized_lines[i-1] != line:
                    total_time += 5
            
            path_details.append((path, transfers, optimized_lines, total_time))

        # 按时间排序
        path_details.sort(key=lambda x: x[3])
        
        return path_details

    def _optimize_path_lines(self, path: List[str]) -> List[str]:
        """优化路径的线路选择，尽量减少换乘次数
        
        Args:
            path: 站点路径列表
            
        Returns:
            List[str]: 优化后的每段线路列表
        """
        if len(path) <= 1:
            return []
            
        # 获取路径中每段可用的线路集合
        segment_lines = []
        for i in range(len(path)-1):
            lines = self.get_line_between_stations(path[i], path[i+1])
            segment_lines.append(lines)
        
        # 现在我们使用动态规划找出最优的线路组合
        # dp[i][line] 表示到第i段，使用line线路的最小换乘次数
        n = len(segment_lines)
        dp = {}
        
        # 初始化第一段
        for line in segment_lines[0]:
            dp[(0, line)] = 0
        
        # 填充dp表
        for i in range(1, n):
            for current_line in segment_lines[i]:
                dp[(i, current_line)] = float('inf')
                for prev_line in segment_lines[i-1]:
                    cost = dp.get((i-1, prev_line), float('inf'))
                    if current_line != prev_line:
                        cost += 1  # 换乘
                    dp[(i, current_line)] = min(dp[(i, current_line)], cost)
        
        # 找出最后一段的最优线路
        min_transfers = float('inf')
        best_last_line = None
        for line in segment_lines[-1]:
            if dp.get((n-1, line), float('inf')) < min_transfers:
                min_transfers = dp.get((n-1, line), float('inf'))
                best_last_line = line
        
        # 回溯找出整个路径的最优线路
        optimal_lines = [best_last_line]
        for i in range(n-1, 0, -1):
            best_prev_line = None
            min_cost = float('inf')
            current_line = optimal_lines[0]
            
            for prev_line in segment_lines[i-1]:
                cost = dp.get((i-1, prev_line), float('inf'))
                if current_line != prev_line:
                    cost += 1
                if cost < min_cost:
                    min_cost = cost
                    best_prev_line = prev_line
            
            optimal_lines.insert(0, best_prev_line)
        
        return optimal_lines

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
                    
                # 获取连接线路集合
                line_set = self.get_line_between_stations(current, next_station)
                if not line_set:
                    continue
                
                # 如果当前已经在使用某条线路，优先使用相同线路避免换乘
                best_line = None
                best_time = float('inf')
                
                for line in line_set:
                    # 计算时间
                    travel_time = self.calculate_travel_time(distance, self.lines[line].speed)
                    # 添加停站时间
                    travel_time += 1
                    # 如果需要换乘，添加换乘时间
                    additional_time = 0
                    if current_line and line != current_line:
                        additional_time = 5  # 换乘时间
                    
                    total_new_time = current_time + travel_time + additional_time
                    
                    # 选择最快的线路
                    if total_new_time < best_time:
                        best_time = total_new_time
                        best_line = line
                
                if best_line and best_time < times[next_station]:
                    times[next_station] = best_time
                    previous[next_station] = current
                    lines_used[next_station] = best_line
                    heapq.heappush(pq, (best_time, best_line, next_station))
        
        # 构建路径
        if times[end] == float('inf'):
            return None, None, None
            
        path = []
        current = end
        path_lines = []
        
        while current:
            path.insert(0, current)
            if previous[current]:
                path_lines.insert(0, lines_used[current])
            current = previous[current]
        
        return path, times[end], path_lines

    def calculate_route_details(self, path: List[str], lines: List[str] = None) -> Dict:
        """计算路径的详细信息"""
        details = {
            "total_distance": 0,
            "total_time": 0,
            "transfers": 0,
            "segments": []
        }
        
        if len(path) <= 1:
            return details
            
        # 如果没有提供线路信息，需要重新计算
        if not lines:
            lines = self._optimize_path_lines(path)
            
        current_line = None
        
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
    path_details = planner.find_least_transfers_path(start, end) 