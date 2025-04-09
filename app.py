# Flask应用主文件
from flask import Flask, render_template, request, jsonify
from services.subway_system import SubwaySystem
from datetime import datetime

#add
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
        result = system.plan_route(start, end, mode)
        return jsonify({"result": result})
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