# Flask应用主文件
from flask import Flask, render_template, request, jsonify
from services.subway_system import SubwaySystem
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

# 创建Flask应用实例
app = Flask(__name__)
# 创建地铁系统实例（全局共享）
system = SubwaySystem()

# 首页路由
@app.route('/')
def index():
    return render_template('index.html')  # 渲染主页模板

# 路线查询API
@app.route('/query', methods=['POST'])
def query():
    data = request.get_json()
    start = data.get('start')
    end = data.get('end')
    mode = data.get('mode', 'time')  # 默认使用最短时间模式
    
    if not start or not end:
        return jsonify({"error": "请提供起点和终点站"}), 400
        
    try:
        # 如果是HTML格式的结果（用于原有页面）
        html_result = system.plan_route(start, end, mode)
        
        # 获取路径数据详情（用于地图显示）
        path_data = system.get_route_details(start, end, mode)
        
        # 对于最少换乘模式，获取所有可能的路线
        all_paths = None
        if mode == 'transfers':
            all_paths = system.get_all_transfer_routes(start, end)
        
        # 合并返回结果
        return jsonify({
            "result": html_result,
            "path": path_data.get("path", []),
            "time": path_data.get("time", 0),
            "transfers": path_data.get("transfers", 0),
            "lines": path_data.get("lines", []),
            "wait_time": path_data.get("wait_time", 0),
            "segments": path_data.get("segments", []),
            "all_paths": all_paths
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

# 添加站点API
@app.route('/edit/add_station', methods=['POST'])
def add_station():
    try:
        data = request.get_json()
        system.editor.add_station(
            line_id=data['line_id'],
            prev_station=data['prev_station'],
            next_station=data['next_station'],
            new_station=data['new_station'],
            prev_distance=float(data['prev_distance']),
            next_distance=float(data['next_distance'])
        )
        # 返回更新后的地铁数据
        return jsonify({
            'success': True, 
            'message': '站点添加成功',
            'data': system.get_system_data()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/edit/remove_station', methods=['POST'])
def remove_station():
    try:
        data = request.get_json()
        system.editor.remove_station(data['station'])
        # 返回更新后的地铁数据
        return jsonify({
            'success': True, 
            'message': '站点删除成功',
            'data': system.get_system_data()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/edit/extend_line', methods=['POST'])
def extend_line():
    try:
        data = request.get_json()
        system.editor.extend_line(
            line_id=data['line_id'],
            terminal_station=data['terminal_station'],
            new_station=data['new_station'],
            distance=float(data['distance'])
        )
        # 返回更新后的地铁数据
        return jsonify({
            'success': True, 
            'message': '线路延长成功',
            'data': system.get_system_data()
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# 添加自定义站点API
@app.route('/edit/add_custom_station', methods=['POST'])
def add_custom_station():
    try:
        data = request.get_json()
        station_data = data['station']
        line_data = data['line']
        is_new_line = data.get('isNewLine', True)
        connections = data.get('connections', {})
        
        # 添加站点到内存数据结构
        new_station_name = station_data['name']
        
        # 创建一个新的站点对象
        from models.station import Station
        new_station = Station(new_station_name)
        
        # 如果是新线路，则创建线路
        if is_new_line:
            from models.line import Line
            new_line = Line(line_data['name'], float(line_data['speed']))
            new_line.stations = [new_station_name]
            
            # 添加到系统
            system.lines[line_data['name']] = new_line
            new_station.add_line(line_data['name'])
            system.stations[new_station_name] = new_station
            
            # 处理与其他站点的连接（如果有）
            if connections and isinstance(connections, dict) and len(connections) > 0:
                for connect_station, distance in connections.items():
                    if connect_station in system.stations:
                        # 建立连接关系，使用用户提供的距离
                        new_station.add_adjacent_station(connect_station, float(distance))
                        system.stations[connect_station].add_adjacent_station(new_station_name, float(distance))
                        print(f"已连接新线路站点 {new_station_name} 和 {connect_station}，距离 {distance} 米")
        else:
            # 如果是已有线路，则连接到线路站点
            line_name = line_data['name']
            line_stations = data.get('lineStations', [])
            
            if line_name in system.lines:
                # 添加站点到线路
                system.lines[line_name].stations = line_stations
                
                # 添加站点到系统
                new_station.add_line(line_name)
                system.stations[new_station_name] = new_station

                # 处理连接信息 - 使用用户提供的距离
                if connections and isinstance(connections, dict) and len(connections) > 0:
                    print(f"收到站点连接信息: {connections}")
                    for connect_station, distance in connections.items():
                        if connect_station in system.stations:
                            # 建立连接关系，使用用户提供的距离
                            new_station.add_adjacent_station(connect_station, float(distance))
                            system.stations[connect_station].add_adjacent_station(new_station_name, float(distance))
                            print(f"已连接站点 {new_station_name} 和 {connect_station}，距离 {distance} 米")
                else:
                    # 如果没有提供连接信息，但提供了站点列表，查找相邻站点
                    if len(line_stations) >= 2:
                        idx = line_stations.index(new_station_name)
                        
                        # 添加与相邻站点的连接关系
                        if idx > 0:
                            prev_station = line_stations[idx - 1]
                            # 这里使用默认距离，因为没有用户提供的具体距离
                            default_distance = 1000  # 默认1000米
                            new_station.add_adjacent_station(prev_station, default_distance)
                            system.stations[prev_station].add_adjacent_station(new_station_name, default_distance)
                            print(f"警告: 使用默认距离 {default_distance}米 连接站点 {new_station_name} 和 {prev_station}")
                        
                        if idx < len(line_stations) - 1:
                            next_station = line_stations[idx + 1]
                            # 这里使用默认距离，因为没有用户提供的具体距离
                            default_distance = 1000  # 默认1000米
                            new_station.add_adjacent_station(next_station, default_distance)
                            system.stations[next_station].add_adjacent_station(new_station_name, default_distance)
                            print(f"警告: 使用默认距离 {default_distance}米 连接站点 {new_station_name} 和 {next_station}")
        
        # 更新站点的经纬度信息（用于前端显示）
        new_station.lat = station_data['lat']
        new_station.lng = station_data['lng']
        
        # 更新规划器
        from services.subway_planner import SubwayPlanner
        system.planner = SubwayPlanner(system.stations, system.lines)
        
        return jsonify({
            'success': True,
            'message': f'站点 {new_station_name} 添加成功',
            'data': {
                'station': new_station_name,
                'line': line_data['name'],
                'systemData': system.get_system_data()
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})

# 计算两点间的距离（米）
def calculate_distance(lat1, lng1, lat2, lng2):
    R = 6371000  # 地球半径（米）
    
    lat1_rad = radians(float(lat1))
    lng1_rad = radians(float(lng1))
    lat2_rad = radians(float(lat2))
    lng2_rad = radians(float(lng2))
    
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    
    a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c  # 返回米为单位的距离

# 添加新的路由来获取地铁数据
@app.route('/get_subway_data')
def get_subway_data():
    return jsonify(system.get_system_data())

# 获取线路发车时间信息
@app.route('/departure_times/<line_id>', methods=['GET'])
def get_departure_times(line_id):
    """获取指定线路的所有发车时间信息"""
    try:
        departure_times = system.get_departure_times(line_id)
        return jsonify({
            'success': True,
            'line_id': line_id,
            'departure_times': departure_times
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

# 获取站点发车时间信息
@app.route('/departure_time', methods=['GET'])
def get_station_departure_time():
    """获取指定线路指定站点的发车时间信息"""
    try:
        line_id = request.args.get('line_id')
        station = request.args.get('station')
        
        if not line_id or not station:
            return jsonify({'success': False, 'message': '请提供线路ID和站点名称'}), 400
            
        departure_time = system.get_station_departure_time(line_id, station)
        
        if departure_time:
            return jsonify({
                'success': True,
                'line_id': line_id,
                'station': station,
                'departure_time': departure_time
            })
        else:
            return jsonify({
                'success': False,
                'message': f'未找到{line_id}线路{station}站的发车时间信息'
            }), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/stations', methods=['GET'])
def get_stations():
    """获取所有站点信息"""
    stations = []
    for station_name, station in system.stations.items():
        stations.append({
            "name": station_name,
            "lines": list(station.lines)
        })
    return jsonify(stations)

@app.route('/click_station', methods=['POST'])
def click_station():
    """处理站点点击事件"""
    data = request.get_json()
    station = data.get('station')
    current_start = data.get('currentStart')
    current_end = data.get('currentEnd')
    
    # 如果没有起点，设置为起点
    if not current_start:
        return jsonify({
            "start": station,
            "end": None,
            "message": f"已选择起点站：{station}"
        })
    
    # 如果有起点但没有终点，设置为终点
    if not current_end:
        return jsonify({
            "start": current_start,
            "end": station,
            "message": f"已选择终点站：{station}"
        })
    
    # 如果起点和终点都已设置，重新开始选择过程
    return jsonify({
        "start": station,
        "end": None,
        "message": f"重新选择，已设置起点站：{station}"
    })

if __name__ == '__main__':
    app.run(debug=True) 