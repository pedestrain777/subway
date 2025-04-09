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
}); 