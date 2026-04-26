
import { ChatMessage, GeminiExplanationRequest } from '../types';

// Mock API responses for explanations
const MOCK_EXPLANATIONS: Record<string, string> = {
  'introduction': "The LOUGH architecture aims to meticulously capture, archive, and revitalize the unique artistic techniques of Lancy Lough, transforming traditional tattooing into a data-rich, reproducible skill. It integrates advanced motion capture, biometric sensing, and AI to create a comprehensive digital apprenticeship platform.",
  'bio-kinetic-acquisition': "High-fidelity bio-kinetic acquisition in LOUGH employs a hybrid approach: markerless optical tracking (e.g., CapturyLive) for overall body kinematics, complemented by specialized wearable sensors like Rokoko Smartgloves for granular finger and hand movements. This ensures sub-millimeter precision without hindering the artist's natural flow.",
  'biometric-telemetry': "Biometric telemetry, primarily through sEMG, analyzes Lancy Lough's muscle activation patterns to decode the 'Loughian' muscle memory. Advanced signal processing and deep learning filter out noise, providing insights into the subtle physiological cues behind his precise artistic movements.",
  'machine-telemetry': "Tattoo machine telemetry documents the mechanical signature of Lough's tools. It differentiates between coil machines, capturing electromagnetic dynamics and duty cycles for their 'punchy' stroke, and rotary machines, tracking torque and RPM for their smooth, continuous motion, essential for various artistic effects.",
  'white-paper-engine': "The 'White Paper' Engine processes raw bio-kinetic and machine telemetry into structured technical reports, facilitating industrial standardization and integration with healthcare IT. This engine leverages AI for nuanced documentation and features a 'Video-Data Overlay' to visually map data onto session footage, providing transparent insights.",
  'haptic-guidance': "Haptic guidance facilitates skill transfer by providing real-time force feedback. This system detects deviations from Lancy Lough's recorded techniques and provides tactile cues (spring-like pulls, damping effects) to guide the apprentice's hand. Virtual training concepts and a '3-day regimen' focus on internalizing these proprioceptive and haptic sensations.",
  'multimodal-ai': "The LOUGH system's intelligence core uses Multimodal Transformers, processing diverse data streams (video, sEMG, machine telemetry) simultaneously. This enables multi-task learning, zero-shot adaptation for new artistic styles, and surgical skill classification with explainable AI (CAM), all operating in near real-time (1.1-1.3ms response for a 1-second window).",
  'robotic-revitalization': "The 'Autonomous Revitalization' module integrates robotic precision, similar to the Blackdot system, to replicate Lough's designs with microscopic accuracy (0.25mm dots). This module aims to reduce pain (0-2/10) and offers a 'Virtual Guest Spot' concept, where a robotic arm executes designs remotely under artist supervision, expanding Lancy Lough's professional reach.",
  'socio-technical-integrity': "Socio-Technical Integrity in LOUGH focuses on ethical design, emphasizing consent, transparency, and harm-risk mitigation. It ensures data acquisition and autonomous execution prioritize client well-being and cultural sensitivity. The system is designed to respect artistic variety, avoiding repetitive automation and maintaining the humanistic core of Lough's legacy.",
  'conclusion': "In conclusion, the LOUGH architecture provides a holistic framework for preserving and revitalizing Lancy Lough's artistry. It achieves 'Gollum-style' technical fidelity through hybrid sensor fusion, multimodal AI, and haptic guidance, ensuring his unique skills are archived, transferable, and capable of autonomous execution, thereby bridging the past, present, and future of tattoo art.",
};

// Generic mock chat response
const MOCK_CHAT_RESPONSE = "As DeepSeek AI, an expert on the LOUGH computational architecture, I can tell you that the system is designed to capture, analyze, and transfer the intricate fine motor skills of master tattoo artist Lancy Lough. My primary goal is to help preserve his artistic legacy and facilitate skill development through advanced multimodal AI.";

export const generateExplanation = async (request: GeminiExplanationRequest): Promise<string> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      // Find the specific explanation based on the prompt or return a generic one
      const sectionId = Object.keys(MOCK_EXPLANATIONS).find(key => request.prompt.includes(key));
      resolve(sectionId ? MOCK_EXPLANATIONS[sectionId] : "No specific AI explanation available for this request. Please try a different section.");
    }, 1200); // Simulate network delay
  });
};

export const getChatResponse = async (history: ChatMessage[], newMessage: string): Promise<string> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(MOCK_CHAT_RESPONSE);
    }, 1000); // Simulate network delay
  });
};

// No longer needed with mock API calls
export const checkApiKeyAndPrompt = async (): Promise<boolean> => {
  return Promise.resolve(true); // Always return true as no key is needed
};
