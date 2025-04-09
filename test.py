from services.subway_system import SubwaySystem
from utils.initializer import initialize_from_json

def test_initialization():
    print("=== 开始初始化测试 ===")
    
    stations, lines = initialize_from_json('resources/data/line_speed_final.json')
    
    # 测试站点初始化
    print("\n=== 测试站点信息 ===")
    test_stations = ["西直门", "北京站", "天安门东"]  # 测试多个站点
    for test_station in test_stations:
        if test_station in stations:
            station = stations[test_station]
            print(f"\n站点名称: {station.name}")
            print(f"所属线路: {station.lines}")
            print(f"相邻站点及距离: {station.adjacent_stations}")
        else:
            print(f"\n未找到站点: {test_station}")
    
    # 测试线路初始化
    print("\n=== 测试线路信息 ===")
    test_lines = ["2号线", "1号线/八通线"]  # 测试多条线路
    for test_line in test_lines:
        if test_line in lines:
            line = lines[test_line]
            print(f"\n线路编号: {line.line_id}")
            print(f"运行速度: {line.speed}km/h")
            print(f"站点列表: {line.stations}")
        else:
            print(f"\n未找到线路: {test_line}")

def test_subway_editor():
    print("\n=== 测试地铁编辑功能 ===")
    
    system = SubwaySystem()
    
    # 测试添加站点
    print("\n1. 测试添加新站点")
    try:
        system.editor.add_station(
            line_id="2号线",
            prev_station="西直门",
            next_station="车公庄",
            new_station="测试站点",
            prev_distance=500,
            next_distance=410
        )
        print("添加站点成功")
    except ValueError as e:
        print(f"添加站点失败：{str(e)}")
    
    # 测试删除站点
    print("\n2. 测试删除站点")
    try:
        system.editor.remove_station("测试站点")
        print("删除站点成功")
    except ValueError as e:
        print(f"删除站点失败：{str(e)}")
    
    # 测试延长线路
    print("\n3. 测试延长线路")
    try:
        system.editor.extend_line(
            line_id="2号线",
            terminal_station="西直门",
            new_station="新站点",
            distance=800
        )
        print("延长线路成功")
    except ValueError as e:
        print(f"延长线路失败：{str(e)}")

def test_subway_editor_error_cases():
    print("\n=== 测试地铁编辑功能错误处理 ===")
    
    system = SubwaySystem()
    
    try:
        # 测试非相邻站点
        print("\n1. 测试在非相邻站点之间添加新站点")
        system.editor.add_station(
            line_id="2号线",
            prev_station="西直门",
            next_station="阜成门",  # 西直门和阜成门之间有车公庄
            new_station="测试站点",
            prev_distance=500,
            next_distance=410
        )
    except ValueError as e:
        print(f"预期的错误：{str(e)}")
    
    try:
        # 测试不存在的线路
        print("\n2. 测试在不存在的线路上添加站点")
        system.editor.add_station(
            line_id="999号线",
            prev_station="西直门",
            next_station="车公庄",
            new_station="测试站点",
            prev_distance=500,
            next_distance=410
        )
    except ValueError as e:
        print(f"预期的错误：{str(e)}")
    
    try:
        # 测试删除不存在的站点
        print("\n3. 测试删除不存在的站点")
        system.editor.remove_station("不存在的站点")
    except ValueError as e:
        print(f"预期的错误：{str(e)}")
    
    try:
        # 测试删除终点站
        print("\n4. 测试删除终点站")
        system.editor.remove_station("积水潭")
    except ValueError as e:
        print(f"预期的错误：{str(e)}")

def test_route_planning():
    print("\n=== 测试路线规划功能 ===")
    
    system = SubwaySystem()
    
    test_cases = [
        ("西直门", "天安门东", "time"),
        ("西直门", "天安门东", "transfers"),
        ("西直门", "积水潭", "time"),
        ("不存在的站点", "天安门东", "time"),
    ]
    
    for start, end, mode in test_cases:
        print(f"\n测试路线: {start} -> {end} (模式: {mode})")
        result = system.plan_route(start, end, mode)
        print(result)

def main():
    try:
        test_initialization()
        test_subway_editor()
        test_subway_editor_error_cases()
        test_route_planning()
        print("\n所有测试完成！")
    except Exception as e:
        print(f"\n测试过程中出现错误：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 