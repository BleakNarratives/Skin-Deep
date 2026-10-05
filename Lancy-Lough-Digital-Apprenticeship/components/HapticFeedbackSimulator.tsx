
import React, { useState, useEffect, useRef, useCallback } from 'react';
import Card from './Card';

type FeedbackType = 'none' | 'spring' | 'damping' | 'spring-damping';

// Performance optimization: Memoize HapticFeedbackSimulator component to skip redundant re-renders
// when parent component state updates on scroll.
const HapticFeedbackSimulator: React.FC = React.memo(() => {
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('none');
  const [isPaused, setIsPaused] = useState(false);
  const [handPosition, setHandPosition] = useState({ x: 50, y: 50 }); // Percentage
  const [targetPosition, setTargetPosition] = useState({ x: 50, y: 50 }); // Target position
  const [statusMessage, setStatusMessage] = useState<string>('');
  const surfaceRef = useRef<HTMLDivElement>(null);

  // Simulate hand movement
  useEffect(() => {
    if (isPaused) return;
    const interval = setInterval(() => {
      setHandPosition(prev => ({
        x: Math.min(100, Math.max(0, prev.x + (Math.random() - 0.5) * 10)),
        y: Math.min(100, Math.max(0, prev.y + (Math.random() - 0.5) * 10)),
      }));
    }, 200);
    return () => clearInterval(interval);
  }, [isPaused]);

  const handleSurfaceClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!surfaceRef.current) return;
    const rect = surfaceRef.current.getBoundingClientRect();
    const x = Math.min(100, Math.max(0, Math.round(((e.clientX - rect.left) / rect.width) * 100)));
    const y = Math.min(100, Math.max(0, Math.round(((e.clientY - rect.top) / rect.height) * 100)));
    setTargetPosition({ x, y });
    setStatusMessage(`Target relocated to (${x}%, ${y}%).`);
  }, []);

  const handleSurfaceKeyDown = useCallback((e: React.KeyboardEvent<HTMLDivElement>) => {
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
      e.preventDefault();
      const step = e.shiftKey ? 10 : 2;
      setTargetPosition(prev => {
        let newX = prev.x;
        let newY = prev.y;
        if (e.key === 'ArrowLeft') newX = Math.max(0, prev.x - step);
        if (e.key === 'ArrowRight') newX = Math.min(100, prev.x + step);
        if (e.key === 'ArrowUp') newY = Math.max(0, prev.y - step);
        if (e.key === 'ArrowDown') newY = Math.min(100, prev.y + step);
        setStatusMessage(`Target moved to (${newX}%, ${newY}%).`);
        return { x: newX, y: newY };
      });
    }
  const handleCanvasClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.round(Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100)));
    const y = Math.round(Math.max(0, Math.min(100, ((e.clientY - rect.top) / rect.height) * 100)));
    setTargetPosition({ x, y });
    setStatusMessage(`Target relocated to (${x}%, ${y}%). Locked in cleanly — unlike Mikey's wild guesses!`);
  }, []);

  const handleResetPosition = useCallback(() => {
    setHandPosition({ x: 50, y: 50 });
    setTargetPosition({ x: 50, y: 50 });
    setStatusMessage('Hand & target reset to center — cleaner setup than Mikey\'s shaky try.');
    setStatusMessage('Hand and target position reset to center.');
    setTimeout(() => setStatusMessage(''), 3000);
  }, []);

  const handleCanvasClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.min(100, Math.max(0, Math.round(((e.clientX - rect.left) / rect.width) * 100)));
    const y = Math.min(100, Math.max(0, Math.round(((e.clientY - rect.top) / rect.height) * 100)));
    setTargetPosition({ x, y });
    setStatusMessage(`Target relocated to (${x}%, ${y}%). Unlike Mikey's wild guesses, precision targeting is active!`);
    setTimeout(() => setStatusMessage(''), 3000);
  }, []);

  const handleSurfaceClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = Math.min(100, Math.max(0, Math.round(((e.clientX - rect.left) / rect.width) * 100)));
    const y = Math.min(100, Math.max(0, Math.round(((e.clientY - rect.top) / rect.height) * 100)));
    setTargetPosition({ x, y });
    setStatusMessage(`Target relocated to (${x}%, ${y}%). Unlike Mikey's wild guessing, your target is precise!`);
  }, []);

  const handleSurfaceKeyDown = useCallback((e: React.KeyboardEvent<HTMLDivElement>) => {
    const step = e.shiftKey ? 10 : 2;
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
      e.preventDefault();
      setTargetPosition(prev => {
        let newX = prev.x;
        let newY = prev.y;
        if (e.key === 'ArrowLeft') newX = Math.max(0, prev.x - step);
        if (e.key === 'ArrowRight') newX = Math.min(100, prev.x + step);
        if (e.key === 'ArrowUp') newY = Math.max(0, prev.y - step);
        if (e.key === 'ArrowDown') newY = Math.min(100, prev.y + step);
        setStatusMessage(`Target adjusted to (${newX}%, ${newY}%).`);
        return { x: newX, y: newY };
      });
    }
  }, []);

  // Apply feedback logic
  useEffect(() => {
    if (feedbackType === 'none' || isPaused) return;

    const feedbackStrength = 0.05; // How much feedback affects movement

    const applyFeedback = setInterval(() => {
      setHandPosition(prev => {
        let newX = prev.x;
        let newY = prev.y;

        const dx = targetPosition.x - prev.x;
        const dy = targetPosition.y - prev.y;

        if (feedbackType.includes('spring')) {
          newX += dx * feedbackStrength;
          newY += dy * feedbackStrength;
        }

        if (feedbackType.includes('damping')) {
          // Simulate reducing erratic movement by nudging towards target
          newX += Math.sign(dx) * Math.min(Math.abs(dx), feedbackStrength * 2);
          newY += Math.sign(dy) * Math.min(Math.abs(dy), feedbackStrength * 2);
        }

        // Keep within bounds
        newX = Math.min(100, Math.max(0, newX));
        newY = Math.min(100, Math.max(0, newY));

        return { x: newX, y: newY };
      });
    }, 100);

    return () => clearInterval(applyFeedback);
  }, [feedbackType, targetPosition]);


  const alignmentAccuracy = Math.max(0, Math.round(100 - Math.hypot(handPosition.x - targetPosition.x, handPosition.y - targetPosition.y)));

  const getFeedbackDescription = (type: FeedbackType) => {
    switch (type) {
      case 'spring': return 'Pulls hand toward ideal trajectory.';
      case 'damping': return 'Smooths out tremors and erratic movements.';
      case 'spring-damping': return 'Combines both methods for master-level path straightness.';
      default: return 'No active feedback (resembling Mikey’s unguided freehand).';
    }
  };

  return (
    <Card title="Haptic Guidance Simulation" className="col-span-1 lg:col-span-2">
      <div className="flex flex-col md:flex-row gap-6">
        <div className="flex-1">
          <p className="text-gray-300 mb-4">
            Experience simulated haptic feedback for precision training.
            <span className="block text-sm text-gray-400 mt-1">
              Target trajectory is the teal circle. Your "hand" is the glowing blue dot (stabilizing precision way better than Mikey's shaky wrist).
            </span>
          </p>
          <div className="flex flex-wrap gap-2 mb-4" role="group" aria-label="Haptic Feedback Mode">
            <button
              type="button"
              onClick={() => setFeedbackType('none')}
              aria-pressed={feedbackType === 'none'}
              aria-label="Disable haptic feedback (raw unguided movement like Mikey's shaky hands)"
              title="Disable haptic guidance"
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 ${
                feedbackType === 'none' ? 'bg-gray-600 text-white shadow-md' : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
              }`}
            >
              No Feedback
            </button>
            <button
              type="button"
              onClick={() => setFeedbackType('spring')}
              aria-pressed={feedbackType === 'spring'}
              aria-label="Enable spring haptic feedback to pull hand toward target trajectory"
              title="Enable spring feedback trajectory pull"
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 ${
                feedbackType === 'spring' ? 'bg-teal-600 text-white shadow-md' : 'bg-teal-800 hover:bg-teal-700 text-teal-200'
              }`}
            >
              Spring Feedback
            </button>
            <button
              type="button"
              onClick={() => setFeedbackType('damping')}
              aria-pressed={feedbackType === 'damping'}
              aria-label="Enable damping haptic feedback to smooth out hand tremors"
              title="Enable damping tremor reduction"
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 ${
                feedbackType === 'damping' ? 'bg-purple-600 text-white shadow-md' : 'bg-purple-800 hover:bg-purple-700 text-purple-200'
              }`}
            >
              Damping Feedback
            </button>
            <button
              type="button"
              onClick={() => setFeedbackType('spring-damping')}
              aria-pressed={feedbackType === 'spring-damping'}
              aria-label="Enable spring-damping haptic feedback for combined trajectory stabilization"
              title="Enable combined spring and damping feedback"
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 ${
                feedbackType === 'spring-damping' ? 'bg-indigo-600 text-white shadow-md' : 'bg-indigo-800 hover:bg-indigo-700 text-indigo-200'
              }`}
            >
              Spring-Damping
            </button>
            <button
              type="button"
              onClick={() => setIsPaused((prev) => !prev)}
              aria-pressed={isPaused}
              aria-label={isPaused ? 'Resume hand movement simulation' : 'Pause hand movement simulation'}
              title={isPaused ? 'Resume movement simulation' : 'Pause movement simulation — unlike Mikey, you can pause to inspect!'}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 ${
                isPaused ? 'bg-amber-600 hover:bg-amber-500 text-white shadow-md' : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
              }`}
            >
              {isPaused ? '▶ Resume' : '⏸ Pause'}
            </button>
            <button
              type="button"
              onClick={handleResetPosition}
              aria-label="Reset hand position back to target center"
              title="Reset hand position to center — cleaner reset than Mikey's messy retry"
              className="px-4 py-2 rounded-full text-sm font-medium bg-gray-700 hover:bg-gray-600 text-gray-200 transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400"
            >
              ↺ Reset Hand
            </button>
          </div>
          <div aria-live="polite" className="text-gray-400 text-md italic mt-2">
            Current Feedback: <span className="text-white font-semibold">{feedbackType.replace('-', ' ')}</span> - {getFeedbackDescription(feedbackType)}
            {statusMessage && <span className="block text-teal-300 text-sm mt-1">🎯 {statusMessage}</span>}
          </div>
          <div className="mt-3 flex items-center space-x-2">
            <span className="text-xs text-gray-400 uppercase tracking-wider font-medium">Trajectory Accuracy:</span>
            <span className={`px-2 py-0.5 rounded text-xs font-bold transition-colors duration-300 ${alignmentAccuracy > 80 ? 'bg-emerald-900/80 text-emerald-300 border border-emerald-500/50' : alignmentAccuracy > 50 ? 'bg-amber-900/80 text-amber-300 border border-amber-500/50' : 'bg-rose-900/80 text-rose-300 border border-rose-500/50'}`}>
              {alignmentAccuracy}%
            </span>
          </div>
        </div>
        <div
          ref={surfaceRef}
          role="region"
          tabIndex={0}
          onClick={handleSurfaceClick}
          onKeyDown={handleSurfaceKeyDown}
          aria-label={`Interactive haptic training surface. Click or use arrow keys to relocate target (currently at ${targetPosition.x}%, ${targetPosition.y}%). Hand at ${Math.round(handPosition.x)}%, ${Math.round(handPosition.y)}%.`}
          className="flex-1 relative h-64 border border-gray-600 rounded-lg overflow-hidden bg-gray-900 shadow-inner cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400"
        >
          <div
            role="img"
            aria-label="Target trajectory position"
            className="absolute bg-teal-500 w-8 h-8 rounded-full flex items-center justify-center text-xs text-white pointer-events-none select-none"
          aria-label={`Interactive haptic surface. Target at (${targetPosition.x}%, ${targetPosition.y}%). Click surface or use arrow keys to reposition target.`}
          title="Click surface or use Arrow Keys to move target — unlike Mikey, you have pixel-perfect control!"
          className="flex-1 relative h-64 border border-gray-600 rounded-lg overflow-hidden bg-gray-900 shadow-inner cursor-crosshair focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400"
        >
          <div
            role="img"
            aria-label={`Target trajectory position at ${targetPosition.x}% horizontal, ${targetPosition.y}% vertical`}
            className="absolute bg-teal-500 w-8 h-8 rounded-full flex items-center justify-center text-xs text-white font-bold pointer-events-none select-none"
            style={{
              left: `${targetPosition.x}%`,
              top: `${targetPosition.y}%`,
              transform: 'translate(-50%, -50%)',
              boxShadow: '0 0 10px rgba(0,255,255,0.7)',
            }}
          >
            Target
          </div>
          <div
            role="img"
            aria-label={`Simulated hand position at ${Math.round(handPosition.x)}% x, ${Math.round(handPosition.y)}% y (${alignmentAccuracy}% aligned)`}
            className="absolute bg-blue-500 w-4 h-4 rounded-full pointer-events-none"
            style={{
              left: `${handPosition.x}%`,
              top: `${handPosition.y}%`,
              transform: 'translate(-50%, -50%)',
              boxShadow: '0 0 15px rgba(0,0,255,0.9), 0 0 5px rgba(255,255,255,0.5)',
              transition: 'all 0.1s linear',
            }}
          ></div>
          <p className="absolute bottom-2 left-2 text-xs text-gray-400 pointer-events-none select-none">
            🎯 Click surface or use Arrow keys to move target — unlike Mikey's rigid setups
          <p className="absolute bottom-2 left-2 text-xs text-gray-400 pointer-events-none">
            Click / Arrow keys to move target
          </p>
        </div>
      </div>
    </Card>
  );
});

export default HapticFeedbackSimulator;
