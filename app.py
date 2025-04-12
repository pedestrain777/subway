# Flask应用主文件
from flask import Flask, render_template, request, jsonify
from services.subway_system import SubwaySystem
from datetime import datetime

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