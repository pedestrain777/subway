from datetime import datetime
from services.subway_system import SubwaySystem

def main():
    system = SubwaySystem()
    
    while True:
        print("\n=== 北京地铁线路查询系统 ===")
        print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n1. 路线查询")
        print("2. 编辑地铁线路")
        print("3. 退出")
        
        choice = input("\n请选择功能 (1-3): ")
        
        if choice == "1":
            start = input("请输入起始站: ")
            end = input("请输入终点站: ")
            print("\n请选择查询模式:")
            print("1. 最短时间")
            print("2. 最少换乘")
            mode = input("请选择 (1-2): ")
            
            mode = "time" if mode == "1" else "transfers"
            result = system.plan_route(start, end, mode)
            print("\n" + result)
            
        elif choice == "2":
            print("\n编辑功能:")
            print("1. 添加站点")
            print("2. 删除站点")
            print("3. 延长线路")
            print("4. 返回主菜单")
            
            edit_choice = input("\n请选择编辑功能 (1-4): ")
            
            if edit_choice == "1":
                line_id = input("请输入线路编号: ")
                prev_station = input("请输入前一站名: ")
                next_station = input("请输入后一站名: ")
                new_station = input("请输入新站点名称: ")
                prev_distance = float(input("请输入与前一站距离(米): "))
                next_distance = float(input("请输入与后一站距离(米): "))
                
                try:
                    system.editor.add_station(line_id, prev_station, next_station,
                                           new_station, prev_distance, next_distance)
                    print("添加成功！")
                except ValueError as e:
                    print(f"错误：{str(e)}")
                    
            elif edit_choice == "2":
                station = input("请输入要删除的站点名称: ")
                try:
                    system.editor.remove_station(station)
                    print("删除成功！")
                except ValueError as e:
                    print(f"错误：{str(e)}")
                    
            elif edit_choice == "3":
                line_id = input("请输入线路编号: ")
                terminal = input("请输入终点站名称: ")
                new_station = input("请输入新站点名称: ")
                distance = float(input("请输入与终点站距离(米): "))
                
                try:
                    system.editor.extend_line(line_id, terminal, new_station, distance)
                    print("延长成功！")
                except ValueError as e:
                    print(f"错误：{str(e)}")
                    
        elif choice == "3":
            print("感谢使用！")
            break
            
        input("\n按回车键继续...")

if __name__ == "__main__":
    main() 