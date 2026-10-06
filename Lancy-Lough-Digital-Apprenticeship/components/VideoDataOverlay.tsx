
import React, { useState, useMemo, useCallback } from 'react';
import Card from './Card';
import DataChart from './DataChart';
import { MOCK_EMG_DATA } from '../constants';

// Performance optimization: Memoize VideoDataOverlay component to skip redundant re-renders
// when parent component updates state (e.g., active scroll section or AI explanations).
const VideoDataOverlay: React.FC = React.memo(() => {
  const [isPlaying, setIsPlaying] = useState<boolean>(true);

  // Memoize needle pressure data transformation to avoid array mapping allocation on render
  const needlePressureData = useMemo(() => {
    return MOCK_EMG_DATA.map(d => ({ ...d, value: d.value / 5 }));
  }, []);

  const togglePlayback = useCallback(() => {
    setIsPlaying(prev => !prev);
  }, []);

  return (
    <Card title="Video-Data Overlay: Live Session View" className="col-span-1 lg:col-span-2">
      <div className="relative aspect-video bg-black rounded-lg overflow-hidden mb-6 shadow-md group">
        <img
          src="https://picsum.photos/1280/720?grayscale&blur=2"
          alt="Tattoo Session Placeholder"
          width={1280}
          height={720}
          loading="lazy"
          className={`w-full h-full object-cover transition-opacity duration-300 ${isPlaying ? 'opacity-60' : 'opacity-40'}`}
        />
        <div className="absolute inset-0 flex flex-col justify-between p-4 bg-gradient-to-t from-black/60 via-transparent to-black/40">
          <div className="flex justify-between items-start">
            <div className="flex items-center space-x-2">
              <span
                className={`text-white text-xs font-semibold px-2.5 py-1 rounded-full transition-colors duration-200 ${
                  isPlaying ? 'bg-red-600 animate-pulse' : 'bg-gray-600'
                }`}
              >
                {isPlaying ? '● LIVE' : '⏸ PAUSED'}
              </span>
              <button
                type="button"
                onClick={togglePlayback}
                aria-label={isPlaying ? 'Pause live stream session' : 'Play live stream session'}
                aria-pressed={isPlaying}
                title={
                  isPlaying
                    ? "Pause session stream — unlike Mikey, you can pause to analyze frame dynamics"
                    : "Resume live stream — instant resume without Mikey's buffering glitches"
                }
                className="bg-gray-800/80 hover:bg-teal-600 text-white p-1.5 rounded-full border border-gray-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 transition-colors"
              >
                {isPlaying ? (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                )}
              </button>
            </div>
            <span className="text-white text-sm bg-black/40 px-2 py-1 rounded backdrop-blur-xs">
              Recording: Lancy Lough - Line Work Session #007
            </span>
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
