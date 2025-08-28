let mapData = null;

// Simple SVG map implementation
function createSVGMap(data) {
    const mapContainer = document.getElementById('map');
    mapContainer.innerHTML = '';
    
    // Find bounds of all points
    let minLat = Infinity, maxLat = -Infinity;
    let minLng = Infinity, maxLng = -Infinity;
    
    [...data.nodes, ...data.inspection].forEach(point => {
        if (point.latitude && point.longitude) {
            minLat = Math.min(minLat, point.latitude);
            maxLat = Math.max(maxLat, point.latitude);
            minLng = Math.min(minLng, point.longitude);
            maxLng = Math.max(maxLng, point.longitude);
        }
    });
    
    // Add padding
    const latPadding = (maxLat - minLat) * 0.1;
    const lngPadding = (maxLng - minLng) * 0.1;
    minLat -= latPadding;
    maxLat += latPadding;
    minLng -= lngPadding;
    maxLng += lngPadding;
    
    const mapWidth = 800;
    const mapHeight = 600;
    
    // Create SVG
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '100%');
    svg.setAttribute('viewBox', `0 0 ${mapWidth} ${mapHeight}`);
    
    // Function to convert lat/lng to x/y
    function latLngToXY(lat, lng) {
        const x = ((lng - minLng) / (maxLng - minLng)) * mapWidth;
        const y = ((maxLat - lat) / (maxLat - minLat)) * mapHeight;
        return { x, y };
    }
    
    // Draw microwave links first (so they appear behind points)
    data.links.forEach(link => {
        if (link.from_lat && link.from_lng && link.to_lat && link.to_lng) {
            const from = latLngToXY(link.from_lat, link.from_lng);
            const to = latLngToXY(link.to_lat, link.to_lng);
            
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            line.setAttribute('x1', from.x);
            line.setAttribute('y1', from.y);
            line.setAttribute('x2', to.x);
            line.setAttribute('y2', to.y);
            line.setAttribute('class', 'map-link');
            line.setAttribute('title', `Link ${link.link_id}: ${link.from_station} → ${link.to_station}`);
            svg.appendChild(line);
        }
    });
    
    // Draw license stations (blue circles)
    data.nodes.forEach(node => {
        if (node.latitude && node.longitude) {
            const pos = latLngToXY(node.latitude, node.longitude);
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', pos.x);
            circle.setAttribute('cy', pos.y);
            circle.setAttribute('r', 4);
            circle.setAttribute('fill', '#1E90FF');
            circle.setAttribute('stroke', '#000');
            circle.setAttribute('stroke-width', 1);
            circle.setAttribute('class', 'map-point');
            circle.setAttribute('data-type', 'license');
            circle.setAttribute('data-info', JSON.stringify({
                type: 'License Station',
                station: node.stn_name || 'N/A',
                client: node.clnt_name || 'N/A',
                freq: node.freq || 'N/A',
                callsign: node.callsign || 'N/A',
                province: node.province || 'N/A',
                city: node.city || 'N/A'
            }));
            svg.appendChild(circle);
        }
    });
    
    // Draw inspection stations (red circles)
    data.inspection.forEach(record => {
        if (record.latitude && record.longitude) {
            const pos = latLngToXY(record.latitude, record.longitude);
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', pos.x);
            circle.setAttribute('cy', pos.y);
            circle.setAttribute('r', 3);
            circle.setAttribute('fill', '#FF4500');
            circle.setAttribute('stroke', '#000');
            circle.setAttribute('stroke-width', 1);
            circle.setAttribute('class', 'map-point');
            circle.setAttribute('data-type', 'inspection');
            circle.setAttribute('data-info', JSON.stringify({
                type: 'Inspection Station',
                station: record.stn_name || 'N/A',
                client: record.clnt_name || 'N/A',
                freq: record.freq || 'N/A',
                status: record.status || 'N/A',
                date: record.tanggal_pemeriksaan || 'N/A'
            }));
            svg.appendChild(circle);
        }
    });
    
    mapContainer.appendChild(svg);
    
    // Add tooltip functionality
    const tooltip = document.createElement('div');
    tooltip.className = 'map-tooltip';
    tooltip.style.display = 'none';
    mapContainer.appendChild(tooltip);
    
    // Add event listeners for tooltips
    svg.addEventListener('mouseover', (e) => {
        if (e.target.classList.contains('map-point')) {
            const info = JSON.parse(e.target.getAttribute('data-info'));
            tooltip.innerHTML = `
                <strong>${info.type}</strong><br>
                Station: ${info.station}<br>
                Client: ${info.client}<br>
                Frequency: ${info.freq}<br>
                ${info.callsign ? `Callsign: ${info.callsign}<br>` : ''}
                ${info.status ? `Status: ${info.status}<br>` : ''}
                ${info.date ? `Date: ${info.date}<br>` : ''}
                ${info.province ? `Province: ${info.province}<br>` : ''}
                ${info.city ? `City: ${info.city}` : ''}
            `;
            tooltip.style.display = 'block';
        }
    });
    
    svg.addEventListener('mousemove', (e) => {
        if (e.target.classList.contains('map-point')) {
            const rect = mapContainer.getBoundingClientRect();
            tooltip.style.left = (e.clientX - rect.left + 10) + 'px';
            tooltip.style.top = (e.clientY - rect.top - 10) + 'px';
        }
    });
    
    svg.addEventListener('mouseout', (e) => {
        if (e.target.classList.contains('map-point')) {
            tooltip.style.display = 'none';
        }
    });
}

// Show message function
function showMessage(message, type = 'info') {
    const messagesContainer = document.getElementById('messages');
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show alert-custom`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    messagesContainer.appendChild(alertDiv);
    
    // Auto dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Upload license data
async function uploadLicense() {
    const fileInput = document.getElementById('licenseFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showMessage('Please select a file first', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showMessage('Uploading license data...', 'info');
        const response = await fetch('/upload_license', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(result.message, 'success');
            refreshStats();
        } else {
            showMessage(result.error, 'danger');
        }
    } catch (error) {
        showMessage('Error uploading file: ' + error.message, 'danger');
    }
}

// Upload inspection data
async function uploadInspection() {
    const fileInput = document.getElementById('inspectionFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showMessage('Please select a file first', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showMessage('Uploading inspection data...', 'info');
        const response = await fetch('/upload_inspection', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(result.message, 'success');
            refreshStats();
        } else {
            showMessage(result.error, 'danger');
        }
    } catch (error) {
        showMessage('Error uploading file: ' + error.message, 'danger');
    }
}

// Load sample data (using the existing files)
async function loadSampleData() {
    try {
        showMessage('Loading sample data...', 'info');
        
        const response = await fetch('/load_sample_data', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(result.message, 'success');
            refreshStats();
        } else {
            showMessage(result.error, 'danger');
        }
        
    } catch (error) {
        showMessage('Error loading sample data: ' + error.message, 'danger');
    }
}

// Refresh statistics
async function refreshStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        if (stats.error) {
            document.getElementById('stats').innerHTML = '<p class="text-danger">Error loading stats</p>';
            return;
        }
        
        const statsHtml = `
            <div class="stats-item">
                <span class="stats-label">License Records:</span>
                <span class="stats-value">${stats.license_records}</span>
            </div>
            <div class="stats-item">
                <span class="stats-label">Inspection Records:</span>
                <span class="stats-value">${stats.inspection_records}</span>
            </div>
            <div class="stats-item">
                <span class="stats-label">Matched Stations:</span>
                <span class="stats-value">${stats.matched_stations}</span>
            </div>
            <div class="stats-item">
                <span class="stats-label">Unique Sites:</span>
                <span class="stats-value">${stats.unique_sites}</span>
            </div>
            <div class="stats-item">
                <span class="stats-label">Unique Links:</span>
                <span class="stats-value">${stats.unique_links}</span>
            </div>
        `;
        
        document.getElementById('stats').innerHTML = statsHtml;
        
    } catch (error) {
        document.getElementById('stats').innerHTML = '<p class="text-danger">Error loading statistics</p>';
    }
}

// Load map data and initialize custom SVG map
async function loadMapData() {
    try {
        showMessage('Loading map data...', 'info');
        
        const response = await fetch('/api/map_data');
        const data = await response.json();
        
        if (data.error) {
            showMessage('Error loading map data: ' + data.error, 'danger');
            return;
        }
        
        mapData = data;
        createSVGMap(data);
        
        showMessage(`Map loaded with ${data.nodes.length} license stations, ${data.inspection.length} inspection records, and ${data.links.length} microwave links`, 'success');
        
    } catch (error) {
        showMessage('Error loading map: ' + error.message, 'danger');
    }
}

// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Load initial stats
    refreshStats();
    
    // Show initial message
    const mapDiv = document.getElementById('map');
    mapDiv.innerHTML = '<div class="text-center"><p>Upload data and click "Load Map Data" to visualize</p></div>';
});