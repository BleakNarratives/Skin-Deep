
import { NavItem, ChartDataPoint, SensorSpec, MachineSpec } from './types';

export const NAV_ITEMS: NavItem[] = [
  { id: 'introduction', name: 'Introduction' },
  { id: 'flash-generator', name: 'Flash Generator' },
  { id: 'bio-kinetic-acquisition', name: 'Bio-Kinetic Acquisition' },
  { id: 'biometric-telemetry', name: 'Biometric Telemetry' },
  { id: 'machine-telemetry', name: 'Machine Telemetry' },
  { id: 'white-paper-engine', name: 'White Paper Engine' },
  { id: 'haptic-guidance', name: 'Haptic Guidance' },
  { id: 'multimodal-ai', name: 'Multimodal AI' },
  { id: 'robotic-revitalization', name: 'Robotic Revitalization' },
  { id: 'socio-technical-integrity', name: 'Socio-Technical Integrity' },
  { id: 'conclusion', name: 'Conclusion' },
];

export const MOCK_EMG_DATA: ChartDataPoint[] = [
  { name: '0s', value: 25 }, { name: '0.1s', value: 30 }, { name: '0.2s', value: 28 },
  { name: '0.3s', value: 35 }, { name: '0.4s', value: 32 }, { name: '0.5s', value: 40 },
  { name: '0.6s', value: 38 }, { name: '0.7s', value: 45 }, { name: '0.8s', value: 42 },
  { name: '0.9s', value: 50 }, { name: '1.0s', value: 48 },
];

export const MOCK_MACHINE_RPM_DATA: ChartDataPoint[] = [
  { name: '0s', value: 8000 }, { name: '0.1s', value: 8100 }, { name: '0.2s', value: 7900 },
  { name: '0.3s', value: 8200 }, { name: '0.4s', value: 8050 }, { name: '0.5s', value: 8300 },
  { name: '0.6s', value: 8150 }, { name: '0.7s', value: 8400 }, { name: '0.8s', value: 8250 },
  { name: '0.9s', value: 8500 }, { name: '1.0s', value: 8350 },
];

export const MOCK_MACHINE_VOLTAGE_DATA: ChartDataPoint[] = [
  { name: '0s', value: 5.5 }, { name: '0.1s', value: 5.8 }, { name: '0.2s', value: 5.6 },
  { name: '0.3s', value: 6.0 }, { name: '0.4s', value: 5.7 }, { name: '0.5s', value: 6.2 },
  { name: '0.6s', value: 5.9 }, { name: '0.7s', value: 6.4 }, { name: '0.8s', value: 6.1 },
  { name: '0.9s', value: 6.5 }, { name: '1.0s', value: 6.3 },
];

export const SENSOR_SPECS: SensorSpec[] = [
  {
    feature: 'Primary Technology',
    rokoko: 'IMU + EMF Sensor Fusion',
    capturyLive: 'Volumetric Optimization (AI)',
    xsens: 'High-Fidelity IMU/Optical',
  },
  {
    feature: 'Tracking Range',
    rokoko: '100m (Untethered WiFi)',
    capturyLive: 'Variable (Camera Setup)',
    xsens: 'Studio-Bound',
  },
  {
    feature: 'Sensor Density',
    rokoko: '7 Sensors per Hand',
    capturyLive: 'Full Body/Fingers/Face',
    xsens: 'Advanced Finger Articulation',
  },
  {
    feature: 'Sample Rate',
    rokoko: '100 fps',
    capturyLive: 'Variable (Gigabit Ethernet)',
    xsens: 'High-Frequency Real-Time',
  },
  {
    feature: 'Environmental Constraint',
    rokoko: 'Cluttered/Dynamic',
    capturyLive: 'Cluttered/Moving Backgrounds',
    xsens: 'Controlled/Studio',
  },
];

export const MACHINE_SPECS: MachineSpec[] = [
  {
    feature: 'Primary Drive',
    coilMachine: 'Electromagnetic Coils/Springs',
    rotaryPen: 'Brushless Motor (12.6 W)',
  },
  {
    feature: 'Feedback Type',
    coilMachine: 'High Vibration/Vocal Buzz',
    rotaryPen: 'Low Vibration/Quiet',
  },
  {
    feature: 'Tuning Method',
    coilMachine: 'Spring/Contact Gap Adjustment',
    rotaryPen: 'Voltage/Stroke Length Change',
  },
  {
    feature: 'Weight',
    coilMachine: '~246 g (Bulkier/Defined)',
    rotaryPen: '~200 g (Pen-like/Balanced)',
  },
  {
    feature: 'Stroke Type',
    coilMachine: 'Rhythmic/Punchy',
    rotaryPen: 'Smooth/Continuous',
  },
];

// Placeholder content for AI explanations to be replaced by actual Gemini calls
export const AI_EXPLANATION_PROMPTS = {
  'introduction': `Explain the core purpose and key integrations of the LOUGH computational architecture in the context of Lancy Lough's digital apprenticeship.`,
  'flash-generator': `Describe the procedural Flash & Stencil Generator, its style/complexity parameters, and the AR Trace Mode for camera-assisted stencil transfer.`,
  'bio-kinetic-acquisition': `Describe the methods used for high-fidelity bio-kinetic data acquisition in LOUGH, focusing on markerless optical tracking and hybrid sensor fusion for finger tracking.`,
  'biometric-telemetry': `Detail how biometric telemetry, specifically sEMG and muscle activation monitoring, contributes to understanding the 'Loughian' technique and the signal processing challenges involved.`,
  'machine-telemetry': `Explain the role of tattoo machine telemetry in the LOUGH system, differentiating between coil and rotary machine dynamics and the data points captured for each.`,
  'white-paper-engine': `Describe the 'White Paper' Engine's function in data synthesis and documentation, including its integration with healthcare IT and the 'Video-Data Overlay' interface.`,
  'haptic-guidance': `Elaborate on the haptic guidance framework for skill transfer, outlining the types of force feedback, virtual training concepts, and the '3-day training regimen'.`,
  'multimodal-ai': `Discuss the intelligence core of LOUGH, focusing on Multimodal Transformers, multi-task learning, zero-shot adaptation, and surgical skill classification for real-time performance.`,
  'robotic-revitalization': `Explain the 'Autonomous Revitalization' module, its connection to systems like Blackdot, mechanisms for pain mitigation, and the 'Virtual Guest Spot' concept.`,
  'socio-technical-integrity': `Articulate the ethical frameworks and principles guiding the LOUGH architecture, emphasizing consent, transparency, harm-risk mitigation, and inclusive dialects for the Lough Legacy.`,
  'conclusion': `Provide a concise summary of how the LOUGH architecture integrates various technologies to preserve and revitalize Lancy Lough's artistry, fulfilling the 'Gollum-style' fidelity requirement.`
};
