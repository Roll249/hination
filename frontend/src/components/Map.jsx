import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';

// Custom marker icons
const createMarkerIcon = (color, size = 24) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        width: ${size}px;
        height: ${size}px;
        background: ${color};
        border: 3px solid white;
        border-radius: 50%;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="
          width: ${size/2}px;
          height: ${size/2}px;
          background: white;
          border-radius: 50%;
        "></div>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size/2, size/2]
  });
};

function Map({ center, districts, selectedDistrict, onDistrictSelect }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef({});
  const [mapReady, setMapReady] = useState(false);

  // Risk color mapping
  const getRiskColor = (districtData) => {
    let risk = 0;
    const c = districtData.current;
    
    // Rainfall risk
    if (c.rainfall > 5) risk += 3;
    else if (c.rainfall > 2) risk += 2;
    else if (c.rainfall > 0.5) risk += 1;
    
    // Humidity risk
    if (c.humidity > 95) risk += 2;
    else if (c.humidity > 85) risk += 1;
    
    // Temperature risk (cold wave)
    if (c.temp < 5) risk += 3;
    else if (c.temp < 10) risk += 2;
    else if (c.temp < 15) risk += 1;

    // Color based on risk
    if (risk >= 5) return '#ef4444'; // severe - red
    if (risk >= 3) return '#f97316'; // high - orange
    if (risk >= 2) return '#eab308'; // moderate - yellow
    return '#22c55e'; // low - green
  };

  // Initialize map
  useEffect(() => {
    if (mapInstanceRef.current) return;

    // Create map
    const map = L.map(mapRef.current, {
      center: center,
      zoom: 10,
      zoomControl: true,
      attributionControl: true
    });

    // Add tile layer (OpenStreetMap)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 18
    }).addTo(map);

    // Add dark theme overlay
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
      maxZoom: 18
    }).addTo(map);

    mapInstanceRef.current = map;
    setMapReady(true);

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Update markers when districts change
  useEffect(() => {
    if (!mapInstanceRef.current || !mapReady) return;

    const map = mapInstanceRef.current;

    // Remove existing markers
    Object.values(markersRef.current).forEach(marker => {
      map.removeLayer(marker);
    });
    markersRef.current = {};

    // Add markers for each district
    Object.entries(districts).forEach(([id, data]) => {
      const riskColor = getRiskColor(data);
      const isSelected = id === selectedDistrict;
      const markerSize = isSelected ? 32 : 24;
      
      const marker = L.marker([data.lat, data.lon], {
        icon: createMarkerIcon(riskColor, markerSize)
      }).addTo(map);

      // Popup content
      const popupContent = `
        <div style="min-width: 200px; padding: 8px;">
          <h3 style="font-weight: 600; margin-bottom: 8px; color: #f1f5f9;">${data.name}</h3>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 13px;">
            <div>
              <span style="color: #94a3b8;">Nhiệt độ</span>
              <div style="color: #f1f5f9; font-weight: 500;">${data.current.temp}°C</div>
            </div>
            <div>
              <span style="color: #94a3b8;">Độ ẩm</span>
              <div style="color: #f1f5f9; font-weight: 500;">${data.current.humidity}%</div>
            </div>
            <div>
              <span style="color: #94a3b8;">Mưa</span>
              <div style="color: #f1f5f9; font-weight: 500;">${data.current.rainfall} mm</div>
            </div>
            <div>
              <span style="color: #94a3b8;">Gió</span>
              <div style="color: #f1f5f9; font-weight: 500;">${data.current.wind_speed} km/h</div>
            </div>
          </div>
          <div style="margin-top: 8px; padding: 6px; background: ${riskColor}20; border-radius: 6px; text-align: center;">
            <span style="color: ${riskColor}; font-weight: 600;">${data.current.weather}</span>
          </div>
        </div>
      `;

      marker.bindPopup(popupContent, {
        className: 'custom-popup'
      });

      marker.on('click', () => {
        onDistrictSelect(id);
      });

      markersRef.current[id] = marker;
    });

    // Fit bounds to show all markers
    const group = L.featureGroup(Object.values(markersRef.current));
    if (Object.keys(districts).length > 1) {
      // map.fitBounds(group.getBounds().pad(0.2));
    }
  }, [districts, selectedDistrict, mapReady]);

  // Update map center when selected district changes
  useEffect(() => {
    if (!mapInstanceRef.current || !center) return;
    mapInstanceRef.current.setView(center, 10, { animate: true });
  }, [center]);

  return (
    <div ref={mapRef} className="w-full h-full">
      {!mapReady && (
        <div className="w-full h-full flex items-center justify-center bg-slate-800">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="mt-4 text-slate-400">Đang tải bản đồ...</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Map;
