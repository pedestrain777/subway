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
        maxZoom: 18,
        // 添加上下文菜单支持
        contextmenu: true,
        contextmenuWidth: 180,
        contextmenuItems: [{
            text: '新建站点',
            callback: showNewStationForm
        }]
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
    
    // 监听右键点击事件（备用）
    subwayMap.on('contextmenu', function(e) {
        // 右键菜单内容由Leaflet-contextmenu插件处理
        console.log("右键点击位置：", e.latlng);
    });
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
    
    // 添加点击事件，增加点击区域和可靠性
    marker.on('click', function() {
        handleMapStationClick(stationName);
    });
    
    // 增加点击区域，提高点击可靠性
    marker.setRadius(6); // 稍微增大点击区域
    
    // 存储标记和标签以便之后访问
    stationMarkers[stationName] = marker;
    stationLabels[stationName] = label;
}

// 绘制地铁线路
function drawSubwayLines() {
    // 清除现有的线路绘制
    if (window.subwayLineObjects) {
        for (const lineId in window.subwayLineObjects) {
            const segments = window.subwayLineObjects[lineId];
            segments.forEach(segment => {
                if (subwayMap.hasLayer(segment.path)) {
                    subwayMap.removeLayer(segment.path);
                }
            });
        }
    }
    
    window.subwayLineObjects = {}; // 存储所有线路对象供后续修改透明度

    // 对于每条线路
    for (const [lineId, lineInfo] of Object.entries(subwayData)) {
        const lineColor = lineColors[lineId] || '#777777';  // 默认颜色
        const stations = lineInfo.stations;
        
        window.subwayLineObjects[lineId] = []; // 存储该线路的所有线段

        // 至少需要两个站点才能绘制线路
        if (stations.length >= 2) {
            for (let i = 0; i < stations.length - 1; i++) {
                const station1 = stations[i];
                const station2 = stations[i + 1];
                
                // 确保两个站点都有经纬度数据
                if (stationData[station1] && stationData[station2]) {
                    const coords1 = [stationData[station1].lat, stationData[station1].lng];
                    const coords2 = [stationData[station2].lat, stationData[station2].lng];
                    
                    // 绘制线路段
                    const linePath = L.polyline([coords1, coords2], {
                        color: lineColor,
                        weight: 3,
                        opacity: 0.7
                    }).addTo(subwayMap);
                    
                    // 添加线路信息提示
                    linePath.bindTooltip(`${lineId}: ${station1} → ${station2}`);
                    
                    // 存储线段对象以便后续修改
                    window.subwayLineObjects[lineId].push({
                        path: linePath,
                        stations: [station1, station2]
                    });
                }
            }
        } else if (stations.length === 1) {
            // 如果线路只有一个站点，添加一个特殊标记
            const station = stations[0];
            if (stationData[station]) {
                const marker = L.circleMarker([stationData[station].lat, stationData[station].lng], {
                    radius: 8,
                    color: lineColor,
                    weight: 3,
                    fillColor: '#ffffff',
                    fillOpacity: 0.8
                }).addTo(subwayMap);
                
                marker.bindTooltip(`${lineId}: ${station} (新建线路起点)`);
                
                // 存储单站点标记
                window.subwayLineObjects[lineId].push({
                    path: marker,
                    stations: [station]
                });
            }
        }
    }
    
    // 更新地图上的活跃路线（如果有）
    if (typeof activeRoutePlanIndex !== 'undefined' && activeRoutePlanIndex >= 0 && mapRoutePlans.length > 0) {
        const plan = mapRoutePlans[activeRoutePlanIndex];
        if (plan && plan.path) {
            updateRouteLineOpacity(plan.path);
        }
    }
}

// 处理地图站点点击事件
function handleMapStationClick(stationName) {
    // 防止重复点击导致的问题
    if (window.isProcessingClick) return;
    window.isProcessingClick = true;
    
    try {
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
    } finally {
        // 确保处理完毕后释放锁定
        setTimeout(() => {
            window.isProcessingClick = false;
        }, 100);
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
    
    // 复原所有线路透明度
    resetAllLineOpacity();
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
        
        // 使用静态高亮效果替代脉动动画
        if (stationMarkers[mapStart]._path && stationMarkers[mapStart]._path.classList) {
            stationMarkers[mapStart]._path.classList.add('station-marker-highlight');
        }
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
        
        // 使用静态高亮效果替代脉动动画
        if (stationMarkers[mapEnd]._path && stationMarkers[mapEnd]._path.classList) {
            stationMarkers[mapEnd]._path.classList.add('station-marker-highlight');
        }
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
        
        // 移除任何高亮效果
        if (marker._path && marker._path.classList) {
            marker._path.classList.remove('route-station-marker');
            marker._path.classList.remove('station-marker-highlight');
        }
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
    
    // 显示加载提示
    document.getElementById('mapSelectionStatus').textContent = `正在规划从 ${start} 到 ${end} 的路线...`;
    
    // 发送请求获取路线
    fetch('/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            start: start,
            end: end,
            mode: mapCurrentMode
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('网络错误，请重试');
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            document.getElementById('mapSelectionStatus').textContent = `查询失败：${data.error}`;
            return;
        }
        
        // 处理返回的路径数据
        if (mapCurrentMode === 'transfers' && data.all_paths && data.all_paths.length > 0) {
            handleMultipleRoutes(data);
        } else {
            handleSingleRoute(data);
        }
    })
    .catch(error => {
        console.error('查询路线失败:', error);
        document.getElementById('mapSelectionStatus').textContent = `查询失败：${error.message}`;
    });
}

// 处理单条路线（最短时间）
function handleSingleRoute(data) {
    // 调整线路透明度
    setRouteLinesOpacity(data);
    
    // 绘制路线
    drawRoutePath(data.path, data.lines);
    
    // 更新选择状态提示
    updateRouteInfo(data);
}

// 处理多条路线（最少换乘）
function handleMultipleRoutes(data) {
    // 存储所有路线方案
    mapRoutePlans = data.all_paths || [];
    if (mapRoutePlans.length === 0) {
        document.getElementById('mapSelectionStatus').textContent = '未找到换乘路线方案';
        return;
    }
    
    // 调整线路透明度 - 先使用第一条路线
    setRouteLinesOpacity(mapRoutePlans[0]);
    
    // 显示路线方案列表
    const routeResultsContainer = document.getElementById('mapRouteResults');
    routeResultsContainer.innerHTML = '<h6 class="mb-3">找到多条换乘方案，点击查看详情：</h6>';
    
    // 为每个路线方案创建UI元素
    mapRoutePlans.forEach((plan, index) => {
        const planDiv = document.createElement('div');
        planDiv.className = 'map-route-plan';
        planDiv.dataset.index = index;
        if (index === 0) planDiv.classList.add('active');
        
        // 路线基本信息
        planDiv.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <span class="map-route-badge" style="background-color: ${index === 0 ? '#007bff' : '#6c757d'}">方案 ${index + 1}</span>
                    换乘次数: ${plan.transfers} | 用时: ${plan.time.toFixed(1)}分钟
                </div>
                <small class="text-muted">票价: ${plan.fare}元</small>
            </div>
            <div class="map-route-lines mt-2">
                ${createLineInfo(plan.lines)}
            </div>
        `;
        
        // 点击事件 - 切换路线显示
        planDiv.addEventListener('click', () => {
            activateRoutePlan(index);
        });
        
        routeResultsContainer.appendChild(planDiv);
    });
    
    // 显示结果容器
    routeResultsContainer.style.display = 'block';
    
    // 默认激活第一条路线
    activateRoutePlan(0);
}

// 激活特定路线方案
function activateRoutePlan(index) {
    if (index < 0 || index >= mapRoutePlans.length) return;
    
    // 更新当前活跃路线索引
    activeRoutePlanIndex = index;
    
    // 清除现有路线
    clearMapRoute();
    
    // 获取所选路线方案
    const plan = mapRoutePlans[index];
    
    // 调整线路透明度
    setRouteLinesOpacity(plan);
    
    // 绘制路线
    drawRoutePath(plan.path, plan.lines);
    
    // 更新路线信息
    updateRouteInfo(plan);
    
    // 更新UI状态 - 高亮选中的方案
    const planElements = document.querySelectorAll('.map-route-plan');
    planElements.forEach(el => {
        el.classList.remove('active');
        // 更新徽章颜色
        const badge = el.querySelector('.map-route-badge');
        if (badge) badge.style.backgroundColor = '#6c757d'; // 默认灰色
    });
    
    const activePlan = document.querySelector(`.map-route-plan[data-index="${index}"]`);
    if (activePlan) {
        activePlan.classList.add('active');
        // 更新徽章颜色
        const badge = activePlan.querySelector('.map-route-badge');
        if (badge) badge.style.backgroundColor = '#007bff'; // 激活蓝色
    }
}

// 更新路线透明度
function updateRouteLineOpacity(path) {
    // 首先将所有线路设为半透明
    for (const lineId in window.subwayLineObjects) {
        const lineSegments = window.subwayLineObjects[lineId];
        lineSegments.forEach(segment => {
            segment.path.setStyle({ opacity: 0.3, weight: 2 });
        });
    }
    
    if (!path || path.length <= 1) return;
    
    // 构建路径站点对的集合，用于快速查找
    const routeSegments = new Set();
    for (let i = 0; i < path.length - 1; i++) {
        const station1 = path[i];
        const station2 = path[i + 1];
        // 按字母顺序排序以确保匹配（因为线段可能是反向存储的）
        const segmentKey = [station1, station2].sort().join('-');
        routeSegments.add(segmentKey);
    }
    
    // 高亮显示路径中的线段
    for (const lineId in window.subwayLineObjects) {
        const lineSegments = window.subwayLineObjects[lineId];
        lineSegments.forEach(segment => {
            const station1 = segment.stations[0];
            const station2 = segment.stations[1];
            const segmentKey = [station1, station2].sort().join('-');
            
            if (routeSegments.has(segmentKey)) {
                // 该线段在规划路径中，设置为完全不透明并加粗
                segment.path.setStyle({ 
                    opacity: 1, 
                    weight: 5,
                    dashArray: null
                });
            }
        });
    }
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
        opacity: 0.8,
        className: 'route-highlight' // 添加高亮样式类
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

// 设置路线透明度
function setRouteLinesOpacity(data) {
    // 首先将所有线路设为半透明
    for (const lineId in window.subwayLineObjects) {
        const lineSegments = window.subwayLineObjects[lineId];
        lineSegments.forEach(segment => {
            segment.path.setStyle({ opacity: 0.3, weight: 2 });
        });
    }
    
    let routePath, routeLines;
    
    // 获取路径和线路信息
    if (data.path && data.lines) {
        routePath = data.path;
        routeLines = data.lines;
    } else if (data.all_paths && data.all_paths.length > 0) {
        // 最少换乘模式，使用第一条路径
        routePath = data.all_paths[0].path;
        routeLines = data.all_paths[0].lines;
    } else {
        return; // 没有路径数据
    }
    
    // 构建路径站点对的集合，用于快速查找
    const routeSegments = new Set();
    for (let i = 0; i < routePath.length - 1; i++) {
        const station1 = routePath[i];
        const station2 = routePath[i + 1];
        // 按字母顺序排序以确保匹配（因为线段可能是反向存储的）
        const segmentKey = [station1, station2].sort().join('-');
        routeSegments.add(segmentKey);
    }
    
    // 高亮显示路径中的线段
    for (const lineId in window.subwayLineObjects) {
        const lineSegments = window.subwayLineObjects[lineId];
        lineSegments.forEach(segment => {
            const station1 = segment.stations[0];
            const station2 = segment.stations[1];
            const segmentKey = [station1, station2].sort().join('-');
            
            if (routeSegments.has(segmentKey)) {
                // 该线段在规划路径中，设置为完全不透明并加粗
                segment.path.setStyle({ 
                    opacity: 1, 
                    weight: 5,
                    dashArray: null
                });
            }
        });
    }
}

// 复原所有线路透明度
function resetAllLineOpacity() {
    if (!window.subwayLineObjects) return;
    
    for (const lineId in window.subwayLineObjects) {
        const lineSegments = window.subwayLineObjects[lineId];
        lineSegments.forEach(segment => {
            segment.path.setStyle({ opacity: 0.7, weight: 3, dashArray: null });
        });
    }
}

// 显示新建站点表单
function showNewStationForm(e) {
    // 保存当前点击的经纬度位置
    const clickedLatlng = e.latlng;
    
    // 创建临时标记，显示在点击位置
    const tempMarker = L.circleMarker([clickedLatlng.lat, clickedLatlng.lng], {
        radius: 8,
        fillColor: '#FF8C00',
        color: '#FF4500',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
    }).addTo(subwayMap);
    
    // 查找最近的站点（仅用于显示参考信息）
    const { closestStation, distance } = findClosestStation(clickedLatlng);
    
    // 获取所有线路下拉选项
    const lineOptions = getLineOptions();
    
    // 创建表单HTML
    const formHtml = `
        <div id="newStationForm" class="card p-3 shadow-sm">
            <h5 class="mb-3">新建站点</h5>
            <div class="mb-3">
                <label for="newStationName" class="form-label">站点名称</label>
                <input type="text" class="form-control" id="newStationName" placeholder="请输入站点名称" required>
            </div>
            <div class="mb-3">
                <label for="newLineName" class="form-label">线路名称</label>
                <select class="form-control" id="newLineName" required>
                    <option value="">请选择线路</option>
                    <option value="new">-- 创建新线路 --</option>
                    ${lineOptions}
                </select>
            </div>
            <div id="newLineSection" class="mb-3" style="display: none;">
                <label for="newLineNameInput" class="form-label">新线路名称</label>
                <input type="text" class="form-control" id="newLineNameInput" placeholder="请输入新线路名称">
            </div>
            <div class="mb-3">
                <label for="lineSpeed" class="form-label">线路平均时速(km/h)</label>
                <input type="number" class="form-control" id="lineSpeed" placeholder="例如：40" value="40" min="1" max="120" required>
            </div>
            <div class="mb-3">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <label class="form-label mb-0">最近站点信息</label>
                    <span class="badge bg-info">${closestStation ? `距离: ${Math.round(distance)}米` : '无附近站点'}</span>
                </div>
                <div class="input-group">
                    <input type="text" class="form-control" id="closestStation" value="${closestStation || ''}" readonly>
                    <button class="btn btn-outline-secondary" type="button" id="refreshClosestStation">刷新</button>
                </div>
                <small class="text-muted">如果选择已有线路，新站点将尝试与此站点连接</small>
            </div>
            <div id="distanceSection" class="mb-3" style="display: none;">
                <label class="form-label">站点距离设置</label>
                <div id="distanceInputs" class="p-2 border rounded">
                    <div class="alert alert-info">
                        选择线路后可设置与连接站点的距离
                    </div>
                </div>
            </div>
            <div class="d-flex justify-content-between">
                <button type="button" class="btn btn-secondary" id="cancelNewStation">取消</button>
                <button type="button" class="btn btn-primary" id="confirmNewStation">创建</button>
            </div>
        </div>
    `;
    
    // 创建表单容器并添加到地图上
    const formContainer = L.popup({
        closeButton: false,
        autoClose: false,
        closeOnEscapeKey: false,
        closeOnClick: false,
        className: 'station-edit-popup',
        maxWidth: 450
    })
    .setLatLng(clickedLatlng)
    .setContent(formHtml)
    .openOn(subwayMap);
    
    // 添加按钮事件处理
    setTimeout(() => {
        // 线路选择事件
        document.getElementById('newLineName').addEventListener('change', function() {
            const newLineSection = document.getElementById('newLineSection');
            const distanceSection = document.getElementById('distanceSection');
            const distanceInputs = document.getElementById('distanceInputs');
            
            // 清空最近站点信息
            const closestStationInput = document.getElementById('closestStation');
            
            if (this.value === 'new') {
                // 创建新线路
                newLineSection.style.display = 'block';
                distanceSection.style.display = 'none';
            } else if (this.value !== '') {
                // 选择已有线路
                newLineSection.style.display = 'none';
                
                // 获取线路上的站点
                const lineStations = subwayData[this.value]?.stations || [];
                
                // 更新最近站点，查找属于该线路的最近站点
                if (lineStations.length > 0) {
                    // 找出线路上距离点击位置最近的站点
                    let closestLineStation = null;
                    let minLineDistance = Infinity;
                    
                    for (const station of lineStations) {
                        if (!stationData[station]) continue;
                        
                        const distance = calculateDistance(
                            clickedLatlng.lat, clickedLatlng.lng,
                            stationData[station].lat, stationData[station].lng
                        );
                        
                        if (distance < minLineDistance) {
                            minLineDistance = distance;
                            closestLineStation = station;
                        }
                    }
                    
                    // 更新显示
                    closestStationInput.value = closestLineStation || '';
                    const badge = document.querySelector('.badge.bg-info');
                    if (badge && closestLineStation) {
                        badge.textContent = `距离: ${Math.round(minLineDistance)}米`;
                    }
                }
                
                // 显示距离输入部分
                distanceSection.style.display = 'block';
                
                // 根据选择的线路生成距离输入框
                let distanceHTML = '';
                if (lineStations.length === 0) {
                    distanceHTML = '<div class="alert alert-warning">所选线路没有站点</div>';
                } else {
                    distanceHTML = '<p class="mb-2">请选择并输入与以下站点的距离（米）：</p>';
                    
                    // 生成单个站点的距离输入HTML
                    function generateStationInputHTML(station, safeStationId, distance, isChecked) {
                        return `
                            <div class="mb-2 border-bottom pb-2">
                                <div class="form-check">
                                    <input class="form-check-input station-connect-check" type="checkbox" 
                                        id="check-${safeStationId}" data-station="${station}"
                                        ${isChecked ? 'checked' : ''}>
                                    <label class="form-check-label" for="check-${safeStationId}">
                                        ${station} <span class="text-muted">(约 ${Math.round(distance)} 米)</span>
                                    </label>
                                </div>
                                <input type="number" class="form-control mt-1" id="distance-${safeStationId}" 
                                    placeholder="与${station}的距离（米）" value="${Math.round(distance)}" 
                                    min="1" ${isChecked ? '' : 'disabled'}>
                            </div>
                        `;
                    }
                    
                    // 如果有最近站点，优先显示它
                    if (closestStationInput.value && lineStations.includes(closestStationInput.value)) {
                        const station = closestStationInput.value;
                        const safeStationId = station.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');
                        const distance = calculateDistance(
                            clickedLatlng.lat, clickedLatlng.lng,
                            stationData[station].lat, stationData[station].lng
                        );
                        
                        distanceHTML += generateStationInputHTML(station, safeStationId, distance, true);
                    }
                    
                    // 对其他站点按距离排序
                    const sortedStations = lineStations
                        .filter(station => station !== closestStationInput.value && stationData[station])
                        .map(station => {
                            const distance = calculateDistance(
                                clickedLatlng.lat, clickedLatlng.lng,
                                stationData[station].lat, stationData[station].lng
                            );
                            return { name: station, distance };
                        })
                        .sort((a, b) => a.distance - b.distance);
                    
                    // 只显示前10个最近的站点
                    sortedStations.slice(0, 10).forEach(({ name, distance }) => {
                        const safeStationId = name.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');
                        distanceHTML += generateStationInputHTML(name, safeStationId, distance, false);
                    });
                    
                    // 如果还有更多站点，显示一个消息
                    if (sortedStations.length > 10) {
                        distanceHTML += `
                            <div class="alert alert-info mt-2">
                                还有 ${sortedStations.length - 10} 个站点未显示。建议使用最近的站点进行连接。
                            </div>
                        `;
                    }
                }
                
                distanceInputs.innerHTML = distanceHTML;
                
                // 添加复选框事件处理
                setTimeout(() => {
                    document.querySelectorAll('.station-connect-check').forEach(checkbox => {
                        checkbox.addEventListener('change', function() {
                            const stationName = this.dataset.station;
                            const safeStationId = stationName.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');
                            const distanceInput = document.getElementById(`distance-${safeStationId}`);
                            if (distanceInput) {
                                distanceInput.disabled = !this.checked;
                            }
                        });
                    });
                }, 0);
            } else {
                // 未选择线路
                newLineSection.style.display = 'none';
                distanceSection.style.display = 'none';
                closestStationInput.value = '';
            }
        });
        
        // 刷新最近站点按钮
        document.getElementById('refreshClosestStation').addEventListener('click', function() {
            // 检查是否选择了线路
            const selectedLine = document.getElementById('newLineName').value;
            if (selectedLine && selectedLine !== 'new' && selectedLine !== '') {
                // 获取线路上的站点
                const lineStations = subwayData[selectedLine]?.stations || [];
                if (lineStations.length > 0) {
                    // 找出线路上距离点击位置最近的站点
                    let closestLineStation = null;
                    let minLineDistance = Infinity;
                    
                    for (const station of lineStations) {
                        const distance = calculateDistance(
                            clickedLatlng.lat, clickedLatlng.lng,
                            stationData[station].lat, stationData[station].lng
                        );
                        
                        if (distance < minLineDistance) {
                            minLineDistance = distance;
                            closestLineStation = station;
                        }
                    }
                    
                    // 更新显示
                    document.getElementById('closestStation').value = closestLineStation || '';
                    const badge = this.closest('.mb-3').querySelector('.badge');
                    if (badge) {
                        badge.textContent = closestLineStation ? `距离: ${Math.round(minLineDistance)}米` : '无附近站点';
                    }
                } else {
                    // 线路没有站点
                    document.getElementById('closestStation').value = '';
                    const badge = this.closest('.mb-3').querySelector('.badge');
                    if (badge) {
                        badge.textContent = '选择的线路没有站点';
                    }
                }
            } else {
                // 没有选择线路，显示所有站点中最近的
                const { closestStation, distance } = findClosestStation(clickedLatlng);
                document.getElementById('closestStation').value = closestStation || '';
                const badge = this.closest('.mb-3').querySelector('.badge');
                if (badge) {
                    badge.textContent = closestStation ? `距离: ${Math.round(distance)}米` : '无附近站点';
                }
            }
            
            // 如果已选择线路，刷新距离输入部分
            if (selectedLine && selectedLine !== 'new' && selectedLine !== '') {
                document.getElementById('newLineName').dispatchEvent(new Event('change'));
            }
        });
        
        // 取消按钮
        document.getElementById('cancelNewStation').addEventListener('click', function() {
            subwayMap.removeLayer(tempMarker);
            subwayMap.closePopup(formContainer);
        });
        
        // 确认按钮
        document.getElementById('confirmNewStation').addEventListener('click', function() {
            const stationName = document.getElementById('newStationName').value.trim();
            let lineName = document.getElementById('newLineName').value;
            const lineSpeed = parseInt(document.getElementById('lineSpeed').value);
            
            // 如果选择创建新线路，使用新线路名称输入框的值
            if (lineName === 'new') {
                lineName = document.getElementById('newLineNameInput').value.trim();
            }
            
            if (!stationName || !lineName || isNaN(lineSpeed) || lineSpeed <= 0) {
                alert('请填写完整的信息！');
                return;
            }
            
            // 检查站点名是否已存在
            if (stationName in stationData) {
                alert('站点名已存在，请使用其他名称！');
                return;
            }
            
            // 获取连接站点及距离信息
            const connections = {};
            
            if (lineName !== 'new' && lineName in subwayData) {
                // 对于已有线路，收集连接站点及距离
                const lineStations = subwayData[lineName]?.stations || [];
                
                if (lineStations.length === 1) {
                    // 如果线路只有一个站点，直接连接
                    const targetStation = lineStations[0];
                    const safeStationId = targetStation.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');
                    const distanceInput = document.getElementById(`distance-${safeStationId}`);
                    if (distanceInput && !isNaN(parseInt(distanceInput.value))) {
                        connections[targetStation] = parseInt(distanceInput.value);
                    }
                } else if (document.getElementById('closestStation').value && 
                           lineStations.includes(document.getElementById('closestStation').value)) {
                    // 如果指定了最近站点，并且该站点在线路上
                    const targetStation = document.getElementById('closestStation').value;
                    const safeStationId = targetStation.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');
                    const distanceInput = document.getElementById(`distance-${safeStationId}`);
                    if (distanceInput && !isNaN(parseInt(distanceInput.value))) {
                        connections[targetStation] = parseInt(distanceInput.value);
                    }
                } else {
                    // 检查选中的连接站点
                    document.querySelectorAll('.station-connect-check:checked').forEach(checkbox => {
                        const stationName = checkbox.dataset.station;
                        const safeStationId = stationName.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');
                        const distanceInput = document.getElementById(`distance-${safeStationId}`);
                        if (distanceInput && !isNaN(parseInt(distanceInput.value))) {
                            connections[stationName] = parseInt(distanceInput.value);
                        }
                    });
                }
                
                // 验证至少选择了一个连接站点（对于已有线路）
                if (Object.keys(connections).length === 0) {
                    alert('请至少选择一个要连接的站点并设置距离！');
                    return;
                }
            }
            
            // 保存新站点信息
            createNewStation(stationName, lineName, lineSpeed, clickedLatlng, connections);
            
            // 关闭表单
            subwayMap.removeLayer(tempMarker);
            subwayMap.closePopup(formContainer);
        });
    }, 100);
}

/**
 * 查找最近的站点
 * @param {Object} position 当前站点的位置
 * @returns {Object} 最近站点及距离
 */
function findClosestStation(position) {
    let closestStation = null;
    let minDistance = Infinity;
    
    // 遍历所有站点查找最近站点
    for (const stationName in stationData) {
        // 不与自己比较
        if (!stationData[stationName]) continue;
        
        const stationPosition = {
            lat: stationData[stationName].lat,
            lng: stationData[stationName].lng
        };
        
        // 计算距离
        const distance = calculateDistance(
            position.lat, position.lng,
            stationPosition.lat, stationPosition.lng
        );
        
        // 更新最近站点
        if (distance > 0 && distance < minDistance) {
            minDistance = distance;
            closestStation = stationName;
        }
    }
    
    return {
        closestStation,
        distance: minDistance
    };
}

/**
 * 使用Haversine公式计算两点间的距离（米）
 */
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000; // 地球半径，单位米
    const dLat = toRadians(lat2 - lat1);
    const dLon = toRadians(lon2 - lon1);
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) * 
        Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
}

function toRadians(degrees) {
    return degrees * (Math.PI / 180);
}

// 获取所有线路选项的HTML
function getLineOptions() {
    return Object.keys(lineColors)
        .map(line => `<option value="${line}">${line}</option>`)
        .join('');
}

// 创建新站点
function createNewStation(stationName, lineName, lineSpeed, latlng, connections) {
    // 添加到站点数据中
    stationData[stationName] = {
        lat: latlng.lat,
        lng: latlng.lng
    };
    
    // 添加站点标记到地图
    addStationMarker(stationName, stationData[stationName]);
    
    // 检查是否是已有线路或新线路
    if (lineName in lineColors) {
        if (Object.keys(connections).length > 0) {
            // 保存连接信息到window对象
            if (!window.stationConnections) {
                window.stationConnections = {};
            }
            
            if (!window.stationConnections[stationName]) {
                window.stationConnections[stationName] = {};
            }
            
            // 为每个连接的站点建立连接关系
            for (const [connectedStation, distance] of Object.entries(connections)) {
                // 保存连接信息
                window.stationConnections[stationName][connectedStation] = distance;
                
                // 建立双向连接
                if (!window.stationConnections[connectedStation]) {
                    window.stationConnections[connectedStation] = {};
                }
                window.stationConnections[connectedStation][stationName] = distance;
                
                console.log(`连接站点：${stationName} <-> ${connectedStation}，距离：${distance}米`);
            }
            
            // 连接到已有线路的一个或多个站点
            connectToExistingLineWithConnections(stationName, lineName, connections);
        } else {
            // 如果没有指定连接，尝试自动连接
            connectToExistingLine(stationName, lineName);
        }
    } else {
        // 新建线路
        createNewLine(stationName, lineName, lineSpeed);
    }
    
    // 保存到服务器
    saveStationToServer(stationName, lineName, lineSpeed, latlng, connections);
    
    // 提示成功
    alert(`站点 "${stationName}" 已创建成功！`);
}

// 使用指定连接信息连接到已有线路
function connectToExistingLineWithConnections(newStationName, lineName, connections) {
    // 获取线路上的所有站点
    const lineStations = subwayData[lineName] ? subwayData[lineName].stations : [];
    
    if (lineStations.length === 0) {
        // 如果该线路不存在或没有站点，创建新线路
        subwayData[lineName] = {
            speed: 40, // 默认速度
            stations: [newStationName]
        };
        
        // 绘制线路
        drawSubwayLines();
        return;
    }
    
    // 确定新站点在线路中的位置
    // 检查连接站点是否包含线路的首站或末站
    const firstStation = lineStations[0];
    const lastStation = lineStations[lineStations.length - 1];
    
    let insertPosition = -1;
    
    // 优先考虑终点站连接（添加到开头或结尾）
    if (firstStation in connections) {
        // 添加到开头
        subwayData[lineName].stations.unshift(newStationName);
        console.log(`添加站点 ${newStationName} 到线路 ${lineName} 的开头`);
    } else if (lastStation in connections) {
        // 添加到结尾
        subwayData[lineName].stations.push(newStationName);
        console.log(`添加站点 ${newStationName} 到线路 ${lineName} 的结尾`);
    } else {
        // 获取连接站点中第一个出现在线路中的站点
        let connectedStationIndex = -1;
        for (const connectedStation of Object.keys(connections)) {
            const index = lineStations.indexOf(connectedStation);
            if (index !== -1) {
                connectedStationIndex = index;
                break;
            }
        }
        
        if (connectedStationIndex === -1) {
            // 如果没有连接站点在线路中，选择最近的站点
            console.log(`没有指定的连接站点在线路 ${lineName} 中，尝试自动连接`);
            connectToExistingLine(newStationName, lineName);
            return;
        }
        
        // 插入到连接站点后面
        subwayData[lineName].stations.splice(connectedStationIndex + 1, 0, newStationName);
        console.log(`添加站点 ${newStationName} 到站点 ${lineStations[connectedStationIndex]} 后面`);
    }
    
    // 重新绘制线路
    drawSubwayLines();
}

// 保存站点到服务器
function saveStationToServer(stationName, lineName, lineSpeed, latlng, connections) {
    // 准备要发送的数据
    const data = {
        station: {
            name: stationName,
            lat: latlng.lat,
            lng: latlng.lng
        },
        line: {
            name: lineName,
            speed: lineSpeed
        },
        isNewLine: !(lineName in lineColors),
        connections: connections || {}
    };
    
    // 如果是已有线路，添加线路站点
    if (!data.isNewLine) {
        data.lineStations = subwayData[lineName].stations;
    }
    
    // 添加与相邻站点的连接和距离信息
    data.connections = {};
    if (window.stationConnections && window.stationConnections[stationName]) {
        data.connections = window.stationConnections[stationName];
    } else if (Object.keys(connections).length > 0) {
        console.log("发送连接信息: ", data.connections);
    }
    
    // 如果有连接信息，则不再需要单独的distance字段
    if (data.connections && Object.keys(data.connections).length > 0) {
        console.log("发送连接信息: ", data.connections);
    }
    
    // 发送到服务器
    fetch('/edit/add_custom_station', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            console.log('站点保存成功：', result);
            
            // 更新站点列表（如有需要）
            updateStationsList();
        } else {
            console.error('保存失败：', result.message);
        }
    })
    .catch(error => {
        console.error('保存过程中出错：', error);
    });
}

// 更新站点列表
function updateStationsList() {
    // 更新datalist
    const stationList = document.getElementById('stationList');
    if (stationList) {
        // 清空现有选项
        stationList.innerHTML = '';
        
        // 添加所有站点
        Object.keys(stationData).forEach(station => {
            const option = document.createElement('option');
            option.value = station;
            stationList.appendChild(option);
        });
    }
    
    // 如果站点查询下拉框需要更新，可以在这里添加
}

// 连接到已有线路
function connectToExistingLine(newStationName, lineName) {
    // 获取线路上的所有站点
    const lineStations = subwayData[lineName] ? subwayData[lineName].stations : [];
    
    if (lineStations.length === 0) {
        // 如果该线路不存在或没有站点，创建新线路
        subwayData[lineName] = {
            speed: 40, // 默认速度
            stations: [newStationName]
        };
        
        // 绘制线路
        drawSubwayLines();
        return;
    }
    
    if (lineStations.length === 1) {
        // 如果线路只有一个站点，直接连接
        const existingStation = lineStations[0];
        
        // 计算两站点间的距离（米）
        const distance = calculateDistance(
            stationData[newStationName].lat,
            stationData[newStationName].lng,
            stationData[existingStation].lat,
            stationData[existingStation].lng
        );
        
        // 更新线路数据
        subwayData[lineName].stations.push(newStationName);
        
        // 保存距离信息 - 创建一个连接信息对象，如果不存在
        if (!window.stationConnections) {
            window.stationConnections = {};
        }
        
        // 保存双向连接的距离
        if (!window.stationConnections[existingStation]) {
            window.stationConnections[existingStation] = {};
        }
        if (!window.stationConnections[newStationName]) {
            window.stationConnections[newStationName] = {};
        }
        
        window.stationConnections[existingStation][newStationName] = distance;
        window.stationConnections[newStationName][existingStation] = distance;
        
        // 日志
        console.log(`连接站点：${existingStation} -> ${newStationName}，距离：${Math.round(distance)}米`);
        
        // 重新绘制线路
        drawSubwayLines();
        return;
    }
    
    // 如果线路有多个站点，找到最近的站点
    let closestStation = null;
    let minDistance = Infinity;
    
    for (const station of lineStations) {
        const distance = calculateDistance(
            stationData[newStationName].lat,
            stationData[newStationName].lng,
            stationData[station].lat,
            stationData[station].lng
        );
        
        if (distance < minDistance) {
            minDistance = distance;
            closestStation = station;
        }
    }
    
    if (closestStation) {
        // 找到最近站点在线路中的索引
        const idx = lineStations.indexOf(closestStation);
        
        // 确定新站点应该插入的位置
        let insertIndex;
        
        if (idx === 0) {
            // 如果最近的站点是起点，新站点放在起点前
            insertIndex = 0;
        } else if (idx === lineStations.length - 1) {
            // 如果最近的站点是终点，新站点放在终点后
            insertIndex = lineStations.length;
        } else {
            // 如果最近的站点在中间，找出应该放在哪个方向
            const prevStation = lineStations[idx - 1];
            const nextStation = lineStations[idx + 1];
            
            const distToPrev = calculateDistance(
                stationData[newStationName].lat,
                stationData[newStationName].lng,
                stationData[prevStation].lat,
                stationData[prevStation].lng
            );
            
            const distToNext = calculateDistance(
                stationData[newStationName].lat,
                stationData[newStationName].lng,
                stationData[nextStation].lat,
                stationData[nextStation].lng
            );
            
            // 放在距离更短的方向
            insertIndex = distToPrev < distToNext ? idx : idx + 1;
        }
        
        // 更新线路数据 - 插入新站点
        subwayData[lineName].stations.splice(insertIndex, 0, newStationName);
        
        // 保存距离信息 - 创建一个连接信息对象，如果不存在
        if (!window.stationConnections) {
            window.stationConnections = {};
        }
        
        // 根据插入位置，确定相邻站点
        const neighbors = [];
        if (insertIndex > 0) {
            neighbors.push(lineStations[insertIndex - 1]);
        }
        if (insertIndex < lineStations.length) {
            neighbors.push(lineStations[insertIndex]);
        }
        
        // 保存与每个相邻站点的距离
        neighbors.forEach(neighbor => {
            const distance = calculateDistance(
                stationData[newStationName].lat,
                stationData[newStationName].lng,
                stationData[neighbor].lat,
                stationData[neighbor].lng
            );
            
            if (!window.stationConnections[neighbor]) {
                window.stationConnections[neighbor] = {};
            }
            if (!window.stationConnections[newStationName]) {
                window.stationConnections[newStationName] = {};
            }
            
            window.stationConnections[neighbor][newStationName] = distance;
            window.stationConnections[newStationName][neighbor] = distance;
            
            // 日志
            console.log(`连接站点：${neighbor} -> ${newStationName}，距离：${Math.round(distance)}米`);
        });
        
        // 重新绘制线路
        drawSubwayLines();
    }
}

// 创建新线路
function createNewLine(stationName, lineName, lineSpeed) {
    // 如果该线路已存在，给出提示
    if (lineName in lineColors) {
        alert(`线路 "${lineName}" 已存在，将尝试连接到该线路`);
        connectToExistingLine(stationName, lineName);
        return;
    }
    
    // 创建新线路
    const color = getRandomColor();
    lineColors[lineName] = color;  // 保存颜色信息
    
    // 添加到地铁数据
    subwayData[lineName] = {
        speed: lineSpeed,
        stations: [stationName]
    };
    
    // 如果该站点附近有其他站点，可以尝试连接
    if (window.stationConnections && stationConnections[stationName]) {
        // 站点已有连接关系，无需额外处理
        console.log(`站点 ${stationName} 已有连接关系：`, stationConnections[stationName]);
    } else {
        // 查找最近的站点并建立连接
        const { closestStation, distance } = findClosestStation({
            lat: stationData[stationName].lat,
            lng: stationData[stationName].lng
        });
        
        if (closestStation && distance < 3000) { // 3公里以内的站点
            // 初始化连接信息
            if (!window.stationConnections) {
                window.stationConnections = {};
            }
            if (!window.stationConnections[stationName]) {
                window.stationConnections[stationName] = {};
            }
            if (!window.stationConnections[closestStation]) {
                window.stationConnections[closestStation] = {};
            }
            
            // 保存距离信息
            window.stationConnections[stationName][closestStation] = distance;
            window.stationConnections[closestStation][stationName] = distance;
            
            console.log(`新线路站点 ${stationName} 与 ${closestStation} 建立连接，距离：${Math.round(distance)}米`);
        }
    }
    
    // 重新绘制线路
    drawSubwayLines();
}

// 生成随机颜色
function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

// 更新路线信息
function updateRouteInfo(data) {
    // 构建换乘线路信息
    let lineInfo = '';
    if (data.lines && data.lines.length > 0) {
        lineInfo = '<div class="map-route-lines">';
        data.lines.forEach(line => {
            const lineColor = lineColors[line] || '#777777';
            lineInfo += `<span class="map-line-badge" style="background-color: ${lineColor};">${line}</span>`;
        });
        lineInfo += '</div>';
    }
    
    // 计算时间和等待时间
    const totalTime = Math.round((data.time || 0) * 10) / 10;
    const waitTime = Math.round((data.wait_time || 0) * 10) / 10;
    
    // 创建路线信息内容
    const routeInfo = `
        <div class="map-route-info">
            <div><b>路线:</b> ${data.path.join(' → ')}</div>
            <div><b>总时间:</b> ${totalTime} 分钟</div>
            <div><b>换乘次数:</b> ${data.transfers || 0} 次</div>
            <div><b>等待时间:</b> ${waitTime} 分钟</div>
            <div><b>票价:</b> ${data.fare || 3} 元</div>
            ${lineInfo}
        </div>
    `;
    
    // 显示路线信息
    document.getElementById('mapSelectionStatus').innerHTML = routeInfo;
} 