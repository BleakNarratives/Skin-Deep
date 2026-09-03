import React, { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import Card from './Card';

type FlashStyle = 'traditional' | 'fineline' | 'blackwork' | 'geometric';

interface GeneratedPath {
  d: string;
  strokeWidth: number;
  fill: string;
  stroke: string;
}

// Seeded PRNG so a given seed always reproduces the same design
function mulberry32(seed: number) {
  return function () {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const VIEWBOX = 400;

function generateOrganicPath(rng: () => number, complexity: number, closed: boolean): string {
  const points: [number, number][] = [];
  const n = 4 + Math.floor(complexity * 1.2);
  const cx = VIEWBOX / 2, cy = VIEWBOX / 2;
  const baseR = VIEWBOX * 0.3;
  for (let i = 0; i < n; i++) {
    const angle = (i / n) * Math.PI * 2;
    const r = baseR * (0.6 + rng() * 0.6);
    points.push([cx + Math.cos(angle) * r, cy + Math.sin(angle) * r]);
  }
  let d = `M ${points[0][0].toFixed(1)} ${points[0][1].toFixed(1)} `;
  for (let i = 0; i < points.length; i++) {
    const p0 = points[i];
    const p1 = points[(i + 1) % points.length];
    const mx = (p0[0] + p1[0]) / 2 + (rng() - 0.5) * 40;
    const my = (p0[1] + p1[1]) / 2 + (rng() - 0.5) * 40;
    d += `Q ${mx.toFixed(1)} ${my.toFixed(1)} ${p1[0].toFixed(1)} ${p1[1].toFixed(1)} `;
    if (!closed && i === points.length - 2) break;
  }
  if (closed) d += 'Z';
  return d;
}

function generateRadialPath(rng: () => number, complexity: number): string {
  const spokes = 3 + Math.floor(complexity / 2);
  const cx = VIEWBOX / 2, cy = VIEWBOX / 2;
  let d = '';
  for (let s = 0; s < spokes; s++) {
    const baseAngle = (s / spokes) * Math.PI * 2;
    const r1 = VIEWBOX * 0.15;
    const r2 = VIEWBOX * (0.3 + rng() * 0.15);
    const jitter = (rng() - 0.5) * 0.3;
    const x1 = cx + Math.cos(baseAngle) * r1;
    const y1 = cy + Math.sin(baseAngle) * r1;
    const x2 = cx + Math.cos(baseAngle + jitter) * r2;
    const y2 = cy + Math.sin(baseAngle + jitter) * r2;
    d += `M ${x1.toFixed(1)} ${y1.toFixed(1)} L ${x2.toFixed(1)} ${y2.toFixed(1)} `;
  }
  return d;
}

function generateFlashDesign(style: FlashStyle, complexity: number, seed: number): GeneratedPath[] {
  const rng = mulberry32(seed);
  const paths: GeneratedPath[] = [];

  switch (style) {
    case 'traditional':
      paths.push({ d: generateOrganicPath(rng, complexity, true), strokeWidth: 6, fill: 'none', stroke: '#111' });
      paths.push({ d: generateOrganicPath(rng, Math.max(2, complexity - 3), true), strokeWidth: 3, fill: 'none', stroke: '#111' });
      break;
    case 'fineline':
      paths.push({ d: generateOrganicPath(rng, complexity, false), strokeWidth: 1.5, fill: 'none', stroke: '#111' });
      break;
    case 'blackwork':
      paths.push({ d: generateOrganicPath(rng, complexity, true), strokeWidth: 0, fill: '#111', stroke: 'none' });
      break;
    case 'geometric':
      paths.push({ d: generateRadialPath(rng, complexity), strokeWidth: 2, fill: 'none', stroke: '#111' });
      break;
  }
  return paths;
}

// Performance optimization: Memoize FlashStencilGenerator component to skip redundant re-renders
// when parent App component updates state (e.g. active scroll section or DeepSeek AI explanations).
const FlashStencilGenerator: React.FC = React.memo(() => {
  const [style, setStyle] = useState<FlashStyle>('traditional');
  const [complexity, setComplexity] = useState(6);
  const [seed, setSeed] = useState(() => Math.floor(Math.random() * 100000));
  const [arMode, setArMode] = useState(false);
  const [overlayScale, setOverlayScale] = useState(1);
  const [overlayOpacity, setOverlayOpacity] = useState(0.7);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);

  // Performance optimization: Memoize flash stencil SVG path generation to avoid costly
  // PRNG and bezier curve mathematical calculations on unrelated re-renders (e.g., overlay scale/opacity changes).
  const paths = React.useMemo(() => generateFlashDesign(style, complexity, seed), [style, complexity, seed]);

  const reroll = useCallback(() => setSeed(Math.floor(Math.random() * 100000)), []);

  useEffect(() => {
    if (!arMode) return;
    navigator.mediaDevices?.getUserMedia({ video: { facingMode: 'environment' } })
      .then((stream) => {
        if (videoRef.current) videoRef.current.srcObject = stream;
      })
      .catch((err) => setCameraError(err.message || 'Camera access denied'));

    return () => {
      const stream = videoRef.current?.srcObject as MediaStream | undefined;
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, [arMode]);

  const downloadSvg = () => {
    const svgContent = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${VIEWBOX} ${VIEWBOX}">
${paths.map(p => `<path d="${p.d}" stroke="${p.stroke}" stroke-width="${p.strokeWidth}" fill="${p.fill}" stroke-linecap="round" stroke-linejoin="round" />`).join('\n')}
</svg>`;
    const blob = new Blob([svgContent], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `flash-${style}-${seed}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card title="Flash & Stencil Generator" className="col-span-1 lg:col-span-2">
      <div className="flex flex-col md:flex-row gap-6">
        <div className="flex-1 space-y-4">
          <div>
            <label htmlFor="flash-style-select" className="text-sm text-gray-400 block mb-1">Style</label>
            <select
              id="flash-style-select"
              value={style}
              onChange={(e) => setStyle(e.target.value as FlashStyle)}
              className="w-full bg-gray-800 text-gray-200 rounded-md px-3 py-2 border border-gray-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 transition-colors"
            >
              <option value="traditional">Traditional</option>
              <option value="fineline">Fine Line</option>
              <option value="blackwork">Blackwork</option>
              <option value="geometric">Geometric</option>
            </select>
          </div>
          <div>
            <label htmlFor="flash-complexity" className="text-sm text-gray-400 block mb-1">Complexity: {complexity}</label>
            <input
              id="flash-complexity"
              type="range" min={2} max={14} value={complexity}
              onChange={(e) => setComplexity(Number(e.target.value))}
              className="w-full focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 rounded-md"
            />
          </div>
          <div className="flex gap-3 flex-wrap">
            <button
              type="button"
              onClick={reroll}
              aria-label="Reroll flash design seed"
              className="px-4 py-2 rounded-full bg-teal-700 hover:bg-teal-600 text-white text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 transition-colors duration-200"
            >
              Reroll
            </button>
            <button
              type="button"
              onClick={downloadSvg}
              aria-label="Download flash stencil as SVG"
              className="px-4 py-2 rounded-full bg-gray-700 hover:bg-gray-600 text-gray-200 text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 transition-colors duration-200"
            >
              Download SVG
            </button>
            <button
              type="button"
              onClick={() => setArMode(!arMode)}
              aria-label={arMode ? 'Exit AR trace mode' : 'Enter AR trace mode'}
              aria-pressed={arMode}
              className={`px-4 py-2 rounded-full text-sm font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 transition-colors duration-200 ${arMode ? 'bg-indigo-600 text-white' : 'bg-indigo-900 text-indigo-200'}`}
            >
              {arMode ? 'Exit AR Trace' : 'AR Trace Mode'}
            </button>
          </div>
          {arMode && (
            <div className="space-y-2 pt-2 border-t border-gray-700">
              <label htmlFor="overlay-scale" className="text-sm text-gray-400 block">Overlay Scale: {overlayScale.toFixed(2)}x</label>
              <input
                id="overlay-scale"
                aria-label={`Overlay scale: ${overlayScale.toFixed(2)}x`}
                type="range" min={0.3} max={2.5} step={0.05} value={overlayScale}
                onChange={(e) => setOverlayScale(Number(e.target.value))}
                className="w-full focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 rounded-md"
              />
              <label htmlFor="overlay-opacity" className="text-sm text-gray-400 block">Overlay Opacity: {Math.round(overlayOpacity * 100)}%</label>
              <input
                id="overlay-opacity"
                aria-label={`Overlay opacity: ${Math.round(overlayOpacity * 100)}%`}
                type="range" min={0.1} max={1} step={0.05} value={overlayOpacity}
                onChange={(e) => setOverlayOpacity(Number(e.target.value))}
                className="w-full focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-400 rounded-md"
              />
              {cameraError && <p className="text-red-400 text-sm" role="alert">{cameraError}</p>}
            </div>
          )}
        </div>

        <div className="flex-1 relative h-80 border border-gray-600 rounded-lg overflow-hidden bg-white">
          {arMode ? (
            <>
              <video ref={videoRef} autoPlay playsInline muted className="absolute inset-0 w-full h-full object-cover" />
              <svg
                viewBox={`0 0 ${VIEWBOX} ${VIEWBOX}`}
                className="absolute inset-0 w-full h-full"
                style={{ opacity: overlayOpacity, transform: `scale(${overlayScale})`, pointerEvents: 'none' }}
              >
                {paths.map((p, i) => (
                  <path key={i} d={p.d} stroke={p.stroke === '#111' ? '#0ff' : p.stroke} strokeWidth={p.strokeWidth}
                    fill={p.fill === '#111' ? 'rgba(0,255,255,0.4)' : p.fill}
                    strokeLinecap="round" strokeLinejoin="round" />
                ))}
              </svg>
            </>
          ) : (
            <svg viewBox={`0 0 ${VIEWBOX} ${VIEWBOX}`} className="w-full h-full">
              {paths.map((p, i) => (
                <path key={i} d={p.d} stroke={p.stroke} strokeWidth={p.strokeWidth} fill={p.fill}
                  strokeLinecap="round" strokeLinejoin="round" />
              ))}
            </svg>
          )}
        </div>
      </div>
    </Card>
  );
});

export default FlashStencilGenerator;
