// 地图变量
let subwayMap;
let stationMarkers = {};
let routePath = null;
let mapStart = null;
let mapEnd = null;
let stationLabels = {}; // 存储站点名称标签
let mapClickState = 0; // 0: 未开始选择, 1: 已选择起点, 2: 已选择终点
let mapCurrentMode = 'time'; // 默认使用最短时间模式
let mapRoutePlans = []; // 存储多个路线方案
let activeRoutePlanIndex = -1; // 当前活跃的路线方案索引

// 地铁线路颜色
const lineColors = {
    "1号线/八通线": "#DC0A31",
    "2号线": "#0054A6",
    "4号线/大兴线": "#008B95",
    "5号线": "#A42AAB",
    "6号线": "#D99F00",
    "7号线": "#F3BD6C",
    "8号线": "#008F92",
    "9号线": "#7BAB09",
    "10号线": "#009DCA",
    "11号线": "#86068D",
    "13号线": "#F6DF00",
    "14号线": "#D6987C",
    "15号线": "#8F0F01",
    "16号线": "#00A090",
    "17号线": "#B3B3B3",
    "19号线": "#D68C01",
    "S1线": "#A8A29A",
    "亦庄线": "#DC1769",
    "房山线": "#E77549",
    "昌平线": "#DE82B1",
    "首都机场线": "#A594C1",
    "大兴机场线": "#005EB4"
};

// 当DOM加载完成后初始化地图
document.addEventListener('DOMContentLoaded', function() {
    // 如果地图标签页是激活状态，直接初始化地图
    if (document.getElementById('map-tab').classList.contains('active')) {
        setTimeout(initMap, 100);
    }

    // 地图标签页事件监听
    document.getElementById('map-tab').addEventListener('click', function() {
        // 当切换到地图标签页时初始化地图
        setTimeout(() => {
            if (!subwayMap) {
                initMap();
            } else {
                // 刷新地图大小以适应容器
                subwayMap.invalidateSize();
            }
        }, 100);
    });

    // 为地图查询按钮添加事件监听
    document.getElementById('queryMapRoute').addEventListener('click', function() {
        const start = document.getElementById('map-start').value;
        const end = document.getElementById('map-end').value;
        
        if (start && end) {
            queryMapRoute(start, end);
        } else {
            alert('请选择起点和终点站点');
        }
    });

    // 为地图重置按钮添加事件监听
    document.getElementById('mapResetSelection').addEventListener('click', function() {
        resetMapSelection();
    });
    
    // 为查询模式切换按钮添加事件监听
    document.querySelectorAll('[data-map-mode]').forEach(btn => {
        btn.addEventListener('click', function() {
            mapCurrentMode = this.dataset.mapMode;
            document.querySelectorAll('[data-map-mode]').forEach(b => 
                b.classList.remove('active'));
            this.classList.add('active');
            
            // 如果已选择起点和终点，自动查询
            if (mapStart && mapEnd) {
                queryMapRoute(mapStart, mapEnd);
            }
        });
    });
    
    // 处理地图输入框变化
    document.getElementById('map-start').addEventListener('change', function() {
        const station = this.value;
        if (isValidStation(station)) {
            mapStart = station;
            mapClickState = mapEnd ? 2 : 1;
            updateMarkerStyles();
            
            // 同步到普通视图
            if (document.getElementById('start')) {
                document.getElementById('start').value = station;
            }
            
            // 更新状态提示
            document.getElementById('mapSelectionStatus').textContent = mapEnd ? 
                `已选择路线：${mapStart} → ${mapEnd}` : '请选择终点站';
                
            // 如果起点和终点都已选择，自动查询路线
            if (mapStart && mapEnd) {
                queryMapRoute(mapStart, mapEnd);
            }
        } else {
            alert('该站点不存在！');
            this.value = '';
            mapStart = null;
        }
    });
    
    document.getElementById('map-end').addEventListener('change', function() {
        const station = this.value;
        if (isValidStation(station)) {
            mapEnd = station;
            mapClickState = 2;
            updateMarkerStyles();
            
            // 同步到普通视图
            if (document.getElementById('end')) {
                document.getElementById('end').value = station;
            }
            
            // 更新状态提示
            document.getElementById('mapSelectionStatus').textContent = mapStart ? 
                `已选择路线：${mapStart} → ${mapEnd}` : '请选择起点站';
                
            // 如果起点和终点都已选择，自动查询路线
            if (mapStart && mapEnd) {
                queryMapRoute(mapStart, mapEnd);
            }
        } else {
            alert('该站点不存在！');
            this.value = '';
            mapEnd = null;
        }
    });
});

// 检查站点是否有效
function isValidStation(stationName) {
    return stationName in stationData;
}

// 初始化地图
function initMap() {
    // 初始化地图，中心设置在北京市中心
    subwayMap = L.map('subway-map', {
        center: [39.9042, 116.4074],
        zoom: 11,
        // 设置最小缩放级别
        minZoom: 9,
        // 设置最大缩放级别
        maxZoom: 18
    });
    
    // 添加OpenStreetMap图层
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(subwayMap);
    
    // 确保地图容器大小正确
    subwayMap.invalidateSize();
    
    // 添加地图控制（缩放控制）
    L.control.zoom({
        position: 'topleft'
    }).addTo(subwayMap);
    
    // 添加所有地铁站标记
    addAllStationMarkers();
    
    // 添加地铁线路
    drawSubwayLines();
    
    // 手动调整地图大小
    resizeMap();
    
    // 添加缩放事件监听器，控制标签显示
    subwayMap.on('zoomend', function() {
        updateLabelsVisibility();
    });
    
    // 初始检查标签可见性
    updateLabelsVisibility();
}

// 添加所有地铁站标记
function addAllStationMarkers() {
    for (const [stationName, coords] of Object.entries(stationData)) {
        addStationMarker(stationName, coords);
    }
}

// 添加单个地铁站标记
function addStationMarker(stationName, coords) {
    // 创建标记
    const marker = L.circleMarker([coords.lat, coords.lng], {
        radius: 5,
        fillColor: '#0078D7',
        color: '#004A83',
        weight: 1,
        opacity: 1,
        fillOpacity: 0.8
    }).addTo(subwayMap);
    
    // 创建站点名称标签
    const label = L.tooltip({
        permanent: true,
        direction: 'top',
        className: 'station-label'
    })
    .setContent(stationName)
    .setLatLng([coords.lat, coords.lng]);
    
    // 仅在缩放级别大于13时显示标签
    subwayMap.on('zoomend', function() {
        if (subwayMap.getZoom() > 13) {
            if (!subwayMap.hasLayer(label)) {
                label.addTo(subwayMap);
            }
        } else {
            if (subwayMap.hasLayer(label)) {
                label.remove();
            }
        }
    });
    
    // 添加点击事件
    marker.on('click', function() {
        handleMapStationClick(stationName);
    });
    
    // 存储标记和标签以便之后访问
    stationMarkers[stationName] = marker;
    stationLabels[stationName] = label;
}

// 绘制地铁线路
function drawSubwayLines() {
    // 对于每条线路
    for (const [lineId, lineInfo] of Object.entries(subwayData)) {
        const lineColor = lineColors[lineId] || '#777777';  // 默认颜色
        const stations = lineInfo.stations;
        
        for (let i = 0; i < stations.length - 1; i++) {
            const station1 = stations[i];
            const station2 = stations[i + 1];
            
            // 确保两个站点都有经纬度数据
            if (stationData[station1] && stationData[station2]) {
                const coords1 = [stationData[station1].lat, stationData[station1].lng];
                const coords2 = [stationData[station2].lat, stationData[station2].lng];
                
                // 绘制线路段
                L.polyline([coords1, coords2], {
                    color: lineColor,
                    weight: 3,
                    opacity: 0.7
                }).addTo(subwayMap);
            }
        }
    }
}

// 处理地图站点点击事件
function handleMapStationClick(stationName) {
    if (mapClickState === 0) {
        // 选择起点
        setAsStart(stationName);
        mapClickState = 1;
    } else if (mapClickState === 1) {
        // 选择终点
        setAsEnd(stationName);
        mapClickState = 2;
        
        // 自动查询路线
        queryMapRoute(mapStart, mapEnd);
    } else {
        // 重新开始选择
        resetMapSelection();
        setAsStart(stationName);
        mapClickState = 1;
    }
}

// 重置地图选择状态
function resetMapSelection() {
    document.getElementById('map-start').value = '';
    document.getElementById('map-end').value = '';
    document.getElementById('mapSelectionStatus').textContent = '请选择或输入起点站';
    mapStart = null;
    mapEnd = null;
    mapClickState = 0;
    
    // 清除路线
    if (routePath) {
        subwayMap.removeLayer(routePath);
        routePath = null;
    }
    
    // 重置所有标记的样式
    resetMarkerStyles();
}

// 设置站点为起点
function setAsStart(stationName) {
    mapStart = stationName;
    document.getElementById('map-start').value = stationName;
    document.getElementById('mapSelectionStatus').textContent = mapEnd ? 
        `已选择路线：${mapStart} → ${mapEnd}` : '请选择终点站';
    
    // 更新标记样式
    updateMarkerStyles();
}

// 设置站点为终点
function setAsEnd(stationName) {
    mapEnd = stationName;
    document.getElementById('map-end').value = stationName;
    document.getElementById('mapSelectionStatus').textContent = mapStart ? 
        `已选择路线：${mapStart} → ${mapEnd}` : '请选择起点站';
    
    // 更新标记样式
    updateMarkerStyles();
}

// 更新标记样式
function updateMarkerStyles() {
    // 重置所有标记样式
    resetMarkerStyles();
    
    // 设置起点标记样式
    if (mapStart && stationMarkers[mapStart]) {
        stationMarkers[mapStart].setStyle({
            radius: 8,
            fillColor: '#FF4500',
            color: '#B22222',
            weight: 2,
            fillOpacity: 1
        });
    }
    
    // 设置终点标记样式
    if (mapEnd && stationMarkers[mapEnd]) {
        stationMarkers[mapEnd].setStyle({
            radius: 8,
            fillColor: '#32CD32',
            color: '#006400',
            weight: 2,
            fillOpacity: 1
        });
    }
}

// 重置所有标记样式
function resetMarkerStyles() {
    for (const marker of Object.values(stationMarkers)) {
        marker.setStyle({
            radius: 5,
            fillColor: '#0078D7',
            color: '#004A83',
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
        });
    }
}

// 查询地图路线
function queryMapRoute(start, end) {
    // 清除现有路线
    clearMapRoute();
    
    // 清空路线方案
    mapRoutePlans = [];
    activeRoutePlanIndex = -1;
    
    // 隐藏路线结果容器
    const routeResultsContainer = document.getElementById('mapRouteResults');
    routeResultsContainer.innerHTML = '';
    routeResultsContainer.style.display = 'none';
    
    // 发送请求获取路线
    fetch('/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            start: start,
            end: end,
            mode: mapCurrentMode  // 使用当前选中的模式
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
            return;
        }
        
        // 处理单条路线（最短时间）或多条路线（最少换乘）
        if (mapCurrentMode === 'time' || !data.all_paths) {
            // 单条路线
            handleSingleRoute(data);
        } else {
            // 多条路线（最少换乘）
            handleMultipleRoutes(data);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('查询失败，请重试');
    });
}

// 处理单条路径（最短时间）
function handleSingleRoute(data) {
    const path = data.path;
    const lines = data.lines || [];
    
    // 存储路线方案
    mapRoutePlans = [{
        path: path,
        lines: lines,
        time: data.time,
        transfers: data.transfers,
        wait_time: data.wait_time || 0,
        segments: data.segments || []
    }];
    
    // 设置为活跃路线
    activeRoutePlanIndex = 0;
    
    // 绘制路线
    drawRoutePath(path, lines);
    
    // 构建换乘线路信息
    let lineInfo = '';
    if (lines && lines.length > 0) {
        lineInfo = '<div class="map-route-lines">';
        lines.forEach(line => {
            const lineColor = lineColors[line] || '#777777';
            lineInfo += `<span class="map-line-badge" style="background-color: ${lineColor};">${line}</span>`;
        });
        lineInfo += '</div>';
    }
    
    // 创建路线信息内容
    const routeInfo = `
        <div class="map-route-info">
            <div><b>路线:</b> ${path.join(' → ')}</div>
            <div><b>总时间:</b> ${Math.round(data.time * 10) / 10} 分钟</div>
            <div><b>换乘次数:</b> ${data.transfers || 0} 次</div>
            <div><b>等待时间:</b> ${Math.round(data.wait_time * 10) / 10} 分钟</div>
            ${lineInfo}
        </div>
    `;
    
    // 显示路线信息
    document.getElementById('mapSelectionStatus').innerHTML = routeInfo;
}

// 处理多条路径（最少换乘）
function handleMultipleRoutes(data) {
    const routeResultsContainer = document.getElementById('mapRouteResults');
    routeResultsContainer.innerHTML = '';
    
    // 获取所有路径
    const paths = data.all_paths || [];
    
    if (paths.length === 0) {
        document.getElementById('mapSelectionStatus').innerHTML = '<div class="text-center">未找到可行路线</div>';
        return;
    }
    
    // 存储所有路线方案
    mapRoutePlans = paths.map(path => ({
        path: path.path,
        lines: path.lines,
        time: path.time,
        transfers: path.transfers,
        wait_time: path.wait_time || 0,
        segments: path.segments || []
    }));
    
    // 创建路线方案列表
    const routePlansHTML = mapRoutePlans.map((plan, index) => {
        const lineInfo = createLineInfo(plan.lines);
        
        // 为每个方案选择不同的颜色
        const colors = ['#007bff', '#28a745', '#fd7e14', '#dc3545', '#6f42c1'];
        const color = colors[index % colors.length];
        
        return `
            <div class="map-route-plan" data-route-index="${index}" style="border-left-color: ${color}">
                <div class="d-flex align-items-center">
                    <span class="map-route-badge" style="background-color: ${color}">方案 ${index+1}</span>
                    <span><b>时间:</b> ${Math.round(plan.time * 10) / 10}分钟 | <b>换乘:</b> ${plan.transfers}次</span>
                </div>
                <div><small>${plan.path.join(' → ')}</small></div>
                ${lineInfo}
            </div>
        `;
    }).join('');
    
    // 显示路线方案列表
    routeResultsContainer.innerHTML = `
        <h6 class="mb-2">最少换乘路线方案 (共${paths.length}条):</h6>
        ${routePlansHTML}
    `;
    routeResultsContainer.style.display = 'block';
    
    // 为每个路线方案添加点击事件
    document.querySelectorAll('.map-route-plan').forEach(el => {
        el.addEventListener('click', function() {
            const index = parseInt(this.dataset.routeIndex);
            activateRoutePlan(index);
        });
    });
    
    // 默认激活第一个路线方案
    activateRoutePlan(0);
    
    // 显示基本信息
    document.getElementById('mapSelectionStatus').innerHTML = `
        <div class="text-center">
            <b>起点:</b> ${data.path[0]} | <b>终点:</b> ${data.path[data.path.length-1]}
            <br>
            <small>请从上方列表中选择一条路线方案</small>
        </div>
    `;
}

// 激活指定的路线方案
function activateRoutePlan(index) {
    if (index < 0 || index >= mapRoutePlans.length) return;
    
    // 更新活跃路线索引
    activeRoutePlanIndex = index;
    
    // 更新UI
    document.querySelectorAll('.map-route-plan').forEach(el => {
        el.classList.remove('active');
    });
    
    const activePlan = document.querySelector(`.map-route-plan[data-route-index="${index}"]`);
    if (activePlan) {
        activePlan.classList.add('active');
    }
    
    // 绘制当前路线
    const plan = mapRoutePlans[index];
    drawRoutePath(plan.path, plan.lines);
}

// 创建线路信息HTML
function createLineInfo(lines) {
    if (!lines || lines.length === 0) return '';
    
    let html = '<div class="map-route-lines">';
    lines.forEach(line => {
        const lineColor = lineColors[line] || '#777777';
        html += `<span class="map-line-badge" style="background-color: ${lineColor};">${line}</span>`;
    });
    html += '</div>';
    
    return html;
}

// 清除地图上的路线
function clearMapRoute() {
    if (routePath) {
        if (Array.isArray(routePath)) {
            routePath.forEach(path => {
                if (path) subwayMap.removeLayer(path);
            });
        } else {
            subwayMap.removeLayer(routePath);
        }
        routePath = null;
    }
}

// 绘制路线路径
function drawRoutePath(stations, lines) {
    // 清除现有路线
    clearMapRoute();
    
    if (!stations || stations.length <= 1) return;
    
    // 多条线路的情况
    if (lines && lines.length > 0) {
        routePath = [];
        let segmentStart = 0;
        let currentLine = lines[0];
        
        // 为每段不同的线路创建不同颜色的路径
        for (let i = 1; i < stations.length; i++) {
            // 检查是否需要换乘
            if (i < lines.length && lines[i] !== currentLine) {
                // 绘制当前线路段
                drawLineSegment(stations.slice(segmentStart, i + 1), currentLine);
                
                // 更新下一段的起点和线路
                segmentStart = i;
                currentLine = lines[i];
            }
        }
        
        // 绘制最后一段线路
        drawLineSegment(stations.slice(segmentStart), currentLine);
    } else {
        // 无线路信息时，使用默认单一颜色
        const coordinates = getCoordinates(stations);
        
        if (coordinates.length > 1) {
            routePath = L.polyline(coordinates, {
                color: '#FF6600',
                weight: 5,
                opacity: 0.8
            }).addTo(subwayMap);
            
            // 将地图视图调整到路线
            subwayMap.fitBounds(routePath.getBounds(), {
                padding: [50, 50]
            });
        }
    }
}

// 绘制单条线路段
function drawLineSegment(stations, line) {
    const coordinates = getCoordinates(stations);
    
    if (coordinates.length <= 1) return;
    
    // 使用线路颜色
    const lineColor = lineColors[line] || '#777777';
    
    // 创建线路段
    const segment = L.polyline(coordinates, {
        color: lineColor,
        weight: 5,
        opacity: 0.8
    }).addTo(subwayMap);
    
    // 存储线路段
    if (Array.isArray(routePath)) {
        routePath.push(segment);
    } else {
        routePath = [segment];
    }
    
    // 将地图视图调整到完整路线
    if (routePath.length === 1) {
        subwayMap.fitBounds(segment.getBounds(), {
            padding: [50, 50]
        });
    }
}

// 获取站点坐标
function getCoordinates(stations) {
    const coordinates = [];
    
    for (const station of stations) {
        if (stationData[station]) {
            coordinates.push([stationData[station].lat, stationData[station].lng]);
        }
    }
    
    return coordinates;
}

// 手动调整地图大小以适应容器
function resizeMap() {
    if (subwayMap) {
        const mapContainer = document.getElementById('subway-map');
        if (mapContainer) {
            // 延迟执行以确保DOM已经完全渲染
            setTimeout(() => {
                subwayMap.invalidateSize();
                console.log('地图大小已调整');
            }, 300);
        }
    }
}

// 监听窗口大小变化，自动调整地图大小
window.addEventListener('resize', resizeMap);

// 监听标签页切换事件
document.addEventListener('shown.bs.tab', function(event) {
    if (event.target.id === 'map-tab') {
        resizeMap();
    }
});

// 更新所有标签的可见性
function updateLabelsVisibility() {
    const currentZoom = subwayMap.getZoom();
    Object.keys(stationLabels).forEach(stationName => {
        const label = stationLabels[stationName];
        if (currentZoom > 13) {
            if (!subwayMap.hasLayer(label)) {
                label.addTo(subwayMap);
            }
        } else {
            if (subwayMap.hasLayer(label)) {
                label.remove();
            }
        }
    });
} 