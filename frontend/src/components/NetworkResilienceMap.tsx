import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { Navigation } from 'lucide-react';

interface PhcMapMarker {
  id: string;
  code: string;
  name: string;
  lat: number;
  lon: number;
  status: 'HEALTHY' | 'WATCH' | 'CRITICAL';
  schHours: number;
  worstService: string;
  bottleneck: string;
}

interface RoadSegment {
  origin: string;
  destination: string;
  lat1: number;
  lon1: number;
  lat2: number;
  lon2: number;
  status: 'OPEN' | 'DEGRADED' | 'BLOCKED';
}

interface NetworkResilienceMapProps {
  phcs?: PhcMapMarker[];
  roads?: RoadSegment[];
  onSelectPhc?: (code: string) => void;
}

// 36 PHCs accurate coordinates matching backend topology
const DEFAULT_MAP_PHCS: PhcMapMarker[] = [
  // District DST-A1 (Base lat 24.5854, lon 73.7125)
  { id: '1', code: 'PHC-DST-A1-01', name: 'PHC North Sector-1', lat: 24.67979, lon: 73.912265, status: 'WATCH', schHours: 54.0, worstService: 'diarrhoeal_care', bottleneck: 'Oral Rehydration Salts' },
  { id: '2', code: 'PHC-DST-A1-02', name: 'PHC North Sector-2', lat: 24.495859, lon: 73.917376, status: 'HEALTHY', schHours: 88.0, worstService: 'maternal_delivery', bottleneck: 'None' },
  { id: '3', code: 'PHC-DST-A1-03', name: 'PHC North Sector-3', lat: 24.45074, lon: 73.710295, status: 'HEALTHY', schHours: 112.0, worstService: 'fever_malaria', bottleneck: 'None' },
  { id: '4', code: 'PHC-DST-A1-04', name: 'PHC North Sector-4', lat: 24.515207, lon: 73.563433, status: 'CRITICAL', schHours: 18.0, worstService: 'diarrhoeal_care', bottleneck: 'Zinc Tablets & ORS' },
  { id: '5', code: 'PHC-DST-A1-05', name: 'PHC North Sector-5', lat: 24.678581, lon: 73.52967, status: 'WATCH', schHours: 50.0, worstService: 'vaccination', bottleneck: 'Solar Cold Chain Battery' },
  { id: '6', code: 'PHC-DST-A1-06', name: 'PHC North Sector-6', lat: 24.858538, lon: 73.690072, status: 'CRITICAL', schHours: 12.0, worstService: 'maternal_delivery', bottleneck: 'Staff Nurse Shortage' },

  // District DST-A2 (Base lat 24.1200, lon 73.9500)
  { id: '7', code: 'PHC-DST-A2-01', name: 'PHC South Sector-1', lat: 24.245497, lon: 74.22809, status: 'HEALTHY', schHours: 96.0, worstService: 'fever_malaria', bottleneck: 'None' },
  { id: '8', code: 'PHC-DST-A2-02', name: 'PHC South Sector-2', lat: 23.963728, lon: 74.173745, status: 'HEALTHY', schHours: 78.0, worstService: 'diarrhoeal_care', bottleneck: 'None' },
  { id: '9', code: 'PHC-DST-A2-03', name: 'PHC South Sector-3', lat: 23.891939, lon: 73.938468, status: 'HEALTHY', schHours: 84.0, worstService: 'vaccination', bottleneck: 'None' },

  // District DST-B1 (Riverine Valley 23.8340, 74.3120)
  { id: '10', code: 'PHC-DST-B1-01', name: 'PHC Barani Sector-1', lat: 23.9500, lon: 74.4500, status: 'WATCH', schHours: 49.0, worstService: 'diarrhoeal_care', bottleneck: 'IV Fluids' },
  { id: '11', code: 'PHC-DST-B1-02', name: 'PHC Barani Sector-2', lat: 23.7500, lon: 74.2100, status: 'CRITICAL', schHours: 16.0, worstService: 'diarrhoeal_care', bottleneck: 'River Inundation Cutoff' },
];

const DEFAULT_MAP_ROADS: RoadSegment[] = [
  { origin: 'PHC-DST-A1-01', destination: 'PHC-DST-A1-02', lat1: 24.67979, lon1: 73.912265, lat2: 24.495859, lon2: 73.917376, status: 'OPEN' },
  { origin: 'PHC-DST-A1-02', destination: 'PHC-DST-A1-03', lat1: 24.495859, lon1: 73.917376, lat2: 24.45074, lon2: 73.710295, status: 'OPEN' },
  { origin: 'PHC-DST-A1-03', destination: 'PHC-DST-A1-04', lat1: 24.45074, lon1: 73.710295, lat2: 24.515207, lon2: 73.563433, status: 'DEGRADED' },
  { origin: 'PHC-DST-A1-04', destination: 'PHC-DST-A1-05', lat1: 24.515207, lon1: 73.563433, lat2: 24.678581, lon2: 73.52967, status: 'BLOCKED' },
  { origin: 'PHC-DST-A1-05', destination: 'PHC-DST-A1-06', lat1: 24.678581, lon1: 73.52967, lat2: 24.858538, lon2: 73.690072, status: 'OPEN' },
];

export const NetworkResilienceMap: React.FC<NetworkResilienceMapProps> = ({
  phcs = DEFAULT_MAP_PHCS,
  roads = DEFAULT_MAP_ROADS,
  onSelectPhc,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      // Initialize Leaflet map
      const map = L.map(mapContainerRef.current, {
        center: [24.45, 73.85],
        zoom: 9,
        zoomControl: false,
      });

      L.control.zoom({ position: 'bottomright' }).addTo(map);

      // CartoDB Positron sleek light basemap tiles
      L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap &copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 19,
      }).addTo(map);

      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;

    // Clear old vector layers
    map.eachLayer((layer) => {
      if (layer instanceof L.Polyline || layer instanceof L.CircleMarker) {
        map.removeLayer(layer);
      }
    });

    // Draw Road Edges with status-based colors
    roads.forEach((road) => {
      let roadColor = '#10b981'; // OPEN
      let dashArray = '';
      if (road.status === 'DEGRADED') {
        roadColor = '#f59e0b';
        dashArray = '5, 5';
      } else if (road.status === 'BLOCKED') {
        roadColor = '#ef4444';
        dashArray = '4, 6';
      }

      L.polyline(
        [
          [road.lat1, road.lon1],
          [road.lat2, road.lon2],
        ],
        {
          color: roadColor,
          weight: road.status === 'BLOCKED' ? 3.5 : 2.5,
          opacity: 0.85,
          dashArray: dashArray,
        }
      ).addTo(map);
    });

    // Draw PHC Markers
    phcs.forEach((phc) => {
      let color = '#10b981';
      if (phc.status === 'WATCH') color = '#f59e0b';
      if (phc.status === 'CRITICAL') color = '#ef4444';

      const circle = L.circleMarker([phc.lat, phc.lon], {
        radius: phc.status === 'CRITICAL' ? 9 : 7.5,
        fillColor: color,
        color: '#ffffff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.95,
      }).addTo(map);

      circle.bindTooltip(
        `<div style="font-family: inherit; font-size: 11px;">
          <strong>${phc.name}</strong> (${phc.code})<br/>
          SCH: <strong>${phc.schHours}h</strong> [${phc.status}]<br/>
          Bottleneck: <em>${phc.bottleneck}</em>
        </div>`,
        { direction: 'top', offset: [0, -8] }
      );

      circle.on('click', () => {
        if (onSelectPhc) onSelectPhc(phc.code);
      });
    });

    // Cleanup on unmount
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [phcs, roads, onSelectPhc]);

  return (
    <div className="panel-card" style={{ padding: '20px' }}>
      <div className="panel-header" style={{ marginBottom: '14px' }}>
        <div className="panel-header-text">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Navigation size={18} color="#0284c7" />
            <h3 style={{ margin: 0 }}>Network Resilience Map</h3>
            <span
              style={{
                fontSize: '0.72rem',
                background: '#e0f2fe',
                color: '#0284c7',
                padding: '2px 8px',
                borderRadius: '6px',
                fontWeight: 600,
              }}
            >
              Leaflet Live GIS
            </span>
          </div>
          <p style={{ margin: '4px 0 0 0' }}>
            Geographic health centers, service capability status, and road passability corridors
          </p>
        </div>

        {/* Legend */}
        <div style={{ display: 'flex', gap: '14px', alignItems: 'center', fontSize: '0.78rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
            <span style={{ color: '#047857', fontWeight: 600 }}>Healthy (&ge;72h)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f59e0b', display: 'inline-block' }} />
            <span style={{ color: '#b45309', fontWeight: 600 }}>Watch (48-72h)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ef4444', display: 'inline-block' }} />
            <span style={{ color: '#b91c1c', fontWeight: 600 }}>Critical (&lt;48h)</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
            <span style={{ width: '14px', height: '3px', background: '#ef4444', display: 'inline-block' }} />
            <span style={{ color: '#b91c1c' }}>Road Blocked</span>
          </div>
        </div>
      </div>

      {/* Leaflet DOM viewport */}
      <div
        ref={mapContainerRef}
        style={{
          width: '100%',
          height: '320px',
          borderRadius: '16px',
          overflow: 'hidden',
          boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.06)',
          border: '1px solid #e2e8f0',
        }}
      />
    </div>
  );
};
