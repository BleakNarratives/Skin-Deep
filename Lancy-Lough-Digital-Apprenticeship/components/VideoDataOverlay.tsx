
import React, { useMemo } from 'react';
import Card from './Card';
import DataChart from './DataChart';
import { MOCK_EMG_DATA } from '../constants';

// Performance optimization: Memoize VideoDataOverlay component to skip redundant re-renders
// when parent component updates state (e.g., active scroll section or AI explanations).
const VideoDataOverlay: React.FC = React.memo(() => {
  // Memoize needle pressure data transformation to avoid array mapping allocation on render
  const needlePressureData = useMemo(() => {
    return MOCK_EMG_DATA.map(d => ({ ...d, value: d.value / 5 }));
  }, []);

  return (
    <Card title="Video-Data Overlay: Live Session View" className="col-span-1 lg:col-span-2">
      <div className="relative aspect-video bg-black rounded-lg overflow-hidden mb-6 shadow-md">
        <img
          src="https://picsum.photos/1280/720?grayscale&blur=2"
          alt="Tattoo Session Placeholder"
          className="w-full h-full object-cover opacity-60"
        />
        <div className="absolute inset-0 flex flex-col justify-between p-4 bg-gradient-to-t from-black/50 to-transparent">
          <div className="flex justify-between items-start">
            <span className="bg-red-600 text-white text-xs px-2 py-1 rounded-full animate-pulse">LIVE</span>
            <span className="text-white text-sm">Recording: Lancy Lough - Line Work Session #007</span>
          </div>
          <div className="flex justify-end items-end gap-4">
            <div className="bg-blue-800 bg-opacity-70 backdrop-blur-sm p-3 rounded-lg text-white text-sm">
              <p>Force: <span className="font-bold text-lg">7.2 N</span></p>
              <p>Depth: <span className="font-bold text-lg">0.8 mm</span></p>
            </div>
            <div className="bg-green-800 bg-opacity-70 backdrop-blur-sm p-3 rounded-lg text-white text-sm">
              <p>RPM: <span className="font-bold text-lg">8200</span></p>
              <p>Duty Cycle: <span className="font-bold text-lg">55%</span></p>
            </div>
          </div>
        </div>
      </div>
      <p className="text-gray-300 text-sm mb-4">
        Visualize biophysical and kinematic data directly mapped onto the video feed of a tattooing session.
        This provides a transparent and harm-risk mitigated environment for research and artistic analysis.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <DataChart
          title="Simulated sEMG Activity (Flexor Carpi Radialis)"
          data={MOCK_EMG_DATA}
          dataKey="value"
          unit="mV"
          color="#82ca9d"
        />
        <DataChart
          title="Simulated Needle Pressure"
          data={needlePressureData}
          dataKey="value"
          unit="g/cm²"
          color="#ffc658"
        />
      </div>
    </Card>
  );
});

export default VideoDataOverlay;
