
import React, { useState, useEffect } from 'react';
import Card from './Card';

type FeedbackType = 'none' | 'spring' | 'damping' | 'spring-damping';

// Performance optimization: Memoize HapticFeedbackSimulator component to skip redundant re-renders
// when parent component state updates on scroll.
const HapticFeedbackSimulator: React.FC = React.memo(() => {
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('none');
  const [handPosition, setHandPosition] = useState({ x: 50, y: 50 }); // Percentage
  const [targetPosition, setTargetPosition] = useState({ x: 50, y: 50 }); // Fixed target

  // Simulate hand movement
  useEffect(() => {
    const interval = setInterval(() => {
      setHandPosition(prev => ({
        x: Math.min(100, Math.max(0, prev.x + (Math.random() - 0.5) * 10)),
        y: Math.min(100, Math.max(0, prev.y + (Math.random() - 0.5) * 10)),
      }));
    }, 200);
    return () => clearInterval(interval);
  }, []);

  // Apply feedback logic
  useEffect(() => {
    if (feedbackType === 'none') return;

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
            <span className="block text-sm text-gray-500">
              Target trajectory represented by the teal circle. Your "hand" is the glowing blue dot.
            </span>
          </p>
          <div className="flex flex-wrap gap-2 mb-4" role="group" aria-label="Haptic Feedback Mode">
            <button
              type="button"
              onClick={() => setFeedbackType('none')}
              aria-pressed={feedbackType === 'none'}
              aria-label="Disable haptic feedback"
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
              aria-label="Enable spring haptic feedback"
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
              aria-label="Enable damping haptic feedback"
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
              aria-label="Enable spring-damping haptic feedback"
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 ${
                feedbackType === 'spring-damping' ? 'bg-indigo-600 text-white shadow-md' : 'bg-indigo-800 hover:bg-indigo-700 text-indigo-200'
              }`}
            >
              Spring-Damping
            </button>
          </div>
          <div aria-live="polite" className="text-gray-400 text-md italic mt-2">
            Current Feedback: <span className="text-white font-semibold">{feedbackType.replace('-', ' ')}</span> - {getFeedbackDescription(feedbackType)}
          </div>
          <div className="mt-3 flex items-center space-x-2">
            <span className="text-xs text-gray-400 uppercase tracking-wider font-medium">Trajectory Accuracy:</span>
            <span className={`px-2 py-0.5 rounded text-xs font-bold transition-colors duration-300 ${alignmentAccuracy > 80 ? 'bg-emerald-900/80 text-emerald-300 border border-emerald-500/50' : alignmentAccuracy > 50 ? 'bg-amber-900/80 text-amber-300 border border-amber-500/50' : 'bg-rose-900/80 text-rose-300 border border-rose-500/50'}`}>
              {alignmentAccuracy}%
            </span>
          </div>
        </div>
        <div
          role="region"
          aria-label="Interactive Haptic Training Canvas"
          className="flex-1 relative h-64 border border-gray-600 rounded-lg overflow-hidden bg-gray-900 shadow-inner"
        >
          <div
            role="img"
            aria-label="Target trajectory center anchor"
            className="absolute bg-teal-500 w-8 h-8 rounded-full flex items-center justify-center text-xs text-white"
            style={{
              left: `${targetPosition.x - 4}%`,
              top: `${targetPosition.y - 4}%`,
              transform: 'translate(-50%, -50%)',
              boxShadow: '0 0 10px rgba(0,255,255,0.7)',
            }}
          >
            Target
          </div>
          <div
            role="img"
            aria-label={`Simulated hand position pointer (${alignmentAccuracy}% aligned)`}
            className="absolute bg-blue-500 w-4 h-4 rounded-full"
            style={{
              left: `${handPosition.x}%`,
              top: `${handPosition.y}%`,
              transform: 'translate(-50%, -50%)',
              boxShadow: '0 0 15px rgba(0,0,255,0.9), 0 0 5px rgba(255,255,255,0.5)',
              transition: 'all 0.1s linear',
            }}
          ></div>
          <p className="absolute bottom-2 left-2 text-xs text-gray-500">Simulated Training Surface</p>
        </div>
      </div>
    </Card>
  );
});

export default HapticFeedbackSimulator;
