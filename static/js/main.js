let currentStart = null;
let currentEnd = null;

function handleStationClick(station) {
    fetch('/click_station', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            station: station,
            currentStart: currentStart,
            currentEnd: currentEnd
        })
    })
    .then(response => response.json())
    .then(data => {
        // 更新当前的起点和终点
        currentStart = data.start;
        currentEnd = data.end;
        
        // 更新输入框显示
        document.getElementById('start').value = currentStart || '';
        document.getElementById('end').value = currentEnd || '';
        
        // 显示提示消息
        if (data.message) {
            // 可以添加一个提示框来显示消息
            alert(data.message);
        }
        
        // 如果起点和终点都已选择，自动查询路线
        if (currentStart && currentEnd) {
            queryRoute();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('操作失败，请重试');
    });
}

// 修改原有的查询函数
function queryRoute() {
    const mode = document.querySelector('input[name="mode"]:checked').value;
    
    fetch('/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            start: currentStart,
            end: currentEnd,
            mode: mode
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            document.getElementById('result').innerHTML = `<p class="error">${data.error}</p>`;
        } else {
            document.getElementById('result').innerHTML = data.result;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('result').innerHTML = '<p class="error">查询失败，请重试</p>';
    });
}

// 为每个站点添加点击事件监听器
document.addEventListener('DOMContentLoaded', function() {
    const stations = document.querySelectorAll('.station');
    stations.forEach(station => {
        station.addEventListener('click', function() {
            handleStationClick(this.textContent.trim());
        });
    });

    // 初始化站点列表
    initializeStationList();
});

// 初始化站点列表
function initializeStationList() {
    const stationList = document.getElementById('stationList');
    const stations = new Set();

    // 从所有线路中收集站点
    Object.values(subwayData).forEach(line => {
        line.stations.forEach(station => {
            stations.add(station);
        });
    });

    // 将站点添加到datalist中
    stations.forEach(station => {
        const option = document.createElement('option');
        option.value = station;
        stationList.appendChild(option);
    });
}

// 处理站点输入
document.getElementById('start').addEventListener('input', function(e) {
    handleStationInput(e.target);
});

document.getElementById('end').addEventListener('input', function(e) {
    handleStationInput(e.target);
});

function handleStationInput(input) {
    const stations = new Set();
    Object.values(subwayData).forEach(line => {
        line.stations.forEach(station => {
            stations.add(station);
        });
    });

    // 验证输入的站点是否存在
    if (input.value && !stations.has(input.value)) {
        input.classList.add('is-invalid');
        updateSelectionStatus('请输入有效的站点名称');
    } else {
        input.classList.remove('is-invalid');
        updateSelectionUI();
    }
}

// 更新选择状态UI
function updateSelectionUI() {
    const start = document.getElementById('start').value;
    const end = document.getElementById('end').value;
    const resetBtn = document.getElementById('resetSelection');
    const status = document.getElementById('selectionStatus');

    if (start && end) {
        resetBtn.disabled = false;
        status.textContent = '已选择起点和终点站';
        document.querySelectorAll('.route-btn').forEach(btn => btn.disabled = false);
    } else if (start) {
        resetBtn.disabled = false;
        status.textContent = '请选择终点站';
        document.querySelectorAll('.route-btn').forEach(btn => btn.disabled = true);
    } else if (end) {
        resetBtn.disabled = false;
        status.textContent = '请选择起点站';
        document.querySelectorAll('.route-btn').forEach(btn => btn.disabled = true);
    } else {
        resetBtn.disabled = true;
        status.textContent = '请选择或输入起点站';
        document.querySelectorAll('.route-btn').forEach(btn => btn.disabled = true);
    }
}

// 重置选择
document.getElementById('resetSelection').addEventListener('click', function() {
    document.getElementById('start').value = '';
    document.getElementById('end').value = '';
    document.querySelectorAll('.station-btn').forEach(btn => btn.classList.remove('selected'));
    updateSelectionUI();
}); 