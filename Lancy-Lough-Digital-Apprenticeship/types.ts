
export interface NavItem {
  id: string;
  name: string;
}

export interface ChatMessage {
  role: 'user' | 'model';
  text: string;
}

export interface ChartDataPoint {
  name: string;
  value: number;
}

export interface SensorSpec {
  feature: string;
  rokoko: string;
  capturyLive: string;
  xsens: string;
}

export interface MachineSpec {
  feature: string;
  coilMachine: string;
  rotaryPen: string;
}

export interface GeminiExplanationRequest {
  prompt: string;
  context?: string;
}
