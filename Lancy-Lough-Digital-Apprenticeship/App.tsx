
import React, { useState, useEffect, useRef, useCallback } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import SectionTitle from './components/SectionTitle';
import Card from './components/Card';
import DataChart from './components/DataChart';
import ChatInterface from './components/ChatInterface';
import HapticFeedbackSimulator from './components/HapticFeedbackSimulator';
import FlashStencilGenerator from './components/FlashStencilGenerator';
import VideoDataOverlay from './components/VideoDataOverlay';
import { NAV_ITEMS, MOCK_EMG_DATA, MOCK_MACHINE_RPM_DATA, MOCK_MACHINE_VOLTAGE_DATA, SENSOR_SPECS, MACHINE_SPECS, AI_EXPLANATION_PROMPTS } from './constants';
import { generateExplanation, checkApiKeyAndPrompt } from './services/geminiService';

const App: React.FC = () => {
  const [activeSection, setActiveSection] = useState<string>('introduction');
  const [geminiExplanations, setGeminiExplanations] = useState<Record<string, string>>({});
  const [loadingExplanation, setLoadingExplanation] = useState<boolean>(true);
  // Removed apiKeyError state as we are mocking API calls

  const sectionRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const fetchExplanation = async (sectionId: string, prompt: string) => {
    setLoadingExplanation(true);
    // Removed apiKeyError related logic
    try {
      // checkApiKeyAndPrompt is now a no-op that always returns true
      await checkApiKeyAndPrompt(); 
      const explanation = await generateExplanation({ prompt });
      setGeminiExplanations((prev) => ({ ...prev, [sectionId]: explanation }));
    } catch (error: any) {
      // Sentinel Security: Avoid exposing raw internal error messages or stack details to the user interface
      console.error(`Error fetching explanation for ${sectionId}`);
      setGeminiExplanations((prev) => ({ ...prev, [sectionId]: "Failed to load AI explanation. Please try again later." }));
    } finally {
      setLoadingExplanation(false);
    }
  };

  useEffect(() => {
    // Fetch initial explanation for the active section
    if (AI_EXPLANATION_PROMPTS[activeSection] && !geminiExplanations[activeSection]) {
      fetchExplanation(activeSection, AI_EXPLANATION_PROMPTS[activeSection]);
    }
  }, [activeSection, geminiExplanations]); // eslint-disable-line react-hooks/exhaustive-deps

  // Performance optimization: Use IntersectionObserver instead of a scroll event listener reading
  // offsetTop/offsetHeight properties. IntersectionObserver runs asynchronously in browser compositor
  // engine threads, eliminating synchronous layout thrashing (forced reflow) and main-thread CPU overhead on scroll.
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visibleEntry = entries.find((entry) => entry.isIntersecting);
        if (visibleEntry) {
          setActiveSection(visibleEntry.target.id);
        }
      },
      {
        rootMargin: '-80px 0px -60% 0px',
        threshold: 0,
      }
    );

    NAV_ITEMS.forEach((item) => {
      const el = sectionRefs.current[item.id];
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const handleSelectSection = useCallback((id: string) => {
    const ref = sectionRefs.current[id];
    if (ref) {
      window.scrollTo({
        top: ref.offsetTop - 70, // Adjust for fixed header
        behavior: 'smooth',
      });
    }
    setActiveSection(id);
    if (AI_EXPLANATION_PROMPTS[id] && !geminiExplanations[id]) {
      fetchExplanation(id, AI_EXPLANATION_PROMPTS[id]);
    }
  }, [geminiExplanations]);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 antialiased">
      <Header />
      <Sidebar navItems={NAV_ITEMS} activeSection={activeSection} onSelectSection={handleSelectSection} />

      <main className="lg:ml-64 pt-20 p-8">
        <div className="container mx-auto">

          {/* AI Explanation Area */}
          <Card className="mb-12 bg-gradient-to-br from-gray-800 to-gray-900 border-l-4 border-teal-500 shadow-2xl">
            <h3 className="text-2xl font-bold text-teal-400 mb-4 flex items-center">
              <img src="https://picsum.photos/30/30" alt="AI Icon" className="mr-3 rounded-full" />
              DeepSeek AI Insights: {NAV_ITEMS.find(item => item.id === activeSection)?.name}
            </h3>
            {loadingExplanation ? (
              <div className="flex items-center text-teal-300 text-lg">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-teal-300" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Fetching DeepSeek AI's wisdom...
              </div>
            ) : (
              <p className="text-gray-200 leading-relaxed text-lg whitespace-pre-wrap">{geminiExplanations[activeSection] || "No AI explanation available for this section."}</p>
            )}
          </Card>

          <section id="introduction" ref={(el) => (sectionRefs.current['introduction'] = el)}>
            <SectionTitle
              id="introduction"
              title="Computational Architecture for the Legacy Overlay Unified Graphics Hub (LOUGH)"
              subtitle="A Multimodal Framework for Bio-Kinetic Archiving and Artistic Revitalization"
            />
            <Card className="mb-12">
              <p className="text-lg leading-relaxed text-gray-200">
                The LANCY LOUGH Tattoo Master Digital Apprenticeship, "Skin Deep," powered by DeepSeek AI, is a pioneering
                initiative to integrate high-fidelity performance capture, biometric telemetry, and autonomous mechanical execution
                to preserve and revitalize the fine motor skill legacy of artist Lancy Lough. This hub codifies Lough's unique
                technical artistry into a living digital repository, fostering skill transfer and artistic evolution.
              </p>
              <p className="mt-4 text-gray-300">
                By synthesizing markerless motion capture, electromagnetic field (EMF) sensor fusion, surface electromyography (sEMG),
                and tattoo machine telemetry, LOUGH creates a multi-task learning environment designed to achieve "Gollum-style"
                fidelity in data capture.
              </p>
            </Card>
          </section>


          <section id="flash-generator" ref={(el) => (sectionRefs.current['flash-generator'] = el)}>
            <SectionTitle
              id="flash-generator"
              title="Flash & Stencil Generator"
              subtitle="Procedural Design Tools with AR Trace Assist"
            />
            <FlashStencilGenerator />
          </section>

          <section id="bio-kinetic-acquisition" ref={(el) => (sectionRefs.current['bio-kinetic-acquisition'] = el)}>
            <SectionTitle
              id="bio-kinetic-acquisition"
              title="High-Fidelity Bio-Kinetic Acquisition"
              subtitle="The Vision and Inertial Layer for 'Gollum-style' Fidelity"
            />
            <Card className="mb-12">
              <p className="text-gray-300 leading-relaxed mb-6">
                The LOUGH architecture's foundational layer focuses on capturing raw kinetic data with sub-millimeter accuracy.
                Achieving "Gollum-style" fidelity for Lancy Lough's fine motor skills involves markerless optical tracking
                (e.g., CapturyLive) and hybrid wearable sensors (e.g., Rokoko Smartgloves). This avoids limitations of
                traditional marker-based systems, which can impede natural movement and fail in cluttered tattoo studio environments.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3">Hybrid Sensor Fusion and Finger Tracking</h3>
              <p className="text-gray-300 leading-relaxed mb-6">
                Rokoko Smartgloves, incorporating IMUs and proprietary EMF sensor fusion, provide pinpoint precision in finger
                placement, critical for replicating Lough's hand movements across surfaces and depths. They capture data at
                100 frames per second (fps) in real-time, ensuring zero lag for high-speed artistic strokes.
              </p>

              <div className="overflow-x-auto">
                <table className="min-w-full bg-gray-800 rounded-lg shadow-md border border-gray-700">
                  <thead>
                    <tr className="bg-gray-700 text-teal-300 uppercase text-sm leading-normal">
                      <th className="py-3 px-6 text-left">Specification</th>
                      <th className="py-3 px-6 text-left">Rokoko Smartgloves (Hybrid)</th>
                      <th className="py-3 px-6 text-left">CapturyLive (Markerless)</th>
                      <th className="py-3 px-6 text-left">Xsens Metagloves by Manus</th>
                    </tr>
                  </thead>
                  <tbody className="text-gray-300 text-sm font-light">
                    {SENSOR_SPECS.map((spec, index) => (
                      <tr key={index} className="border-b border-gray-600 hover:bg-gray-700">
                        <td className="py-3 px-6 text-left whitespace-nowrap font-medium text-white">{spec.feature}</td>
                        <td className="py-3 px-6 text-left">{spec.rokoko}</td>
                        <td className="py-3 px-6 text-left">{spec.capturyLive}</td>
                        <td className="py-3 px-6 text-left">{spec.xsens}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </section>

          <section id="biometric-telemetry" ref={(el) => (sectionRefs.current['biometric-telemetry'] = el)}>
            <SectionTitle
              id="biometric-telemetry"
              title="Biometric Telemetry and the Internal State"
              subtitle="Documenting the 'Loughian' Muscle Memory"
            />
            <Card className="mb-12">
              <p className="text-gray-300 leading-relaxed mb-6">
                To capture the artist's internal intent, LOUGH integrates a biometric layer with surface Electromyography (sEMG)
                and muscle activation monitoring, vital for documenting Lough's technique, which relies on specific muscle tension
                patterns. The Delsys Trigno system provides high-fidelity sEMG combined with accelerometry and gyroscopy.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3">Deep Learning for Signal Reconstruction</h3>
              <p className="text-gray-300 leading-relaxed mb-4">
                Noisy sEMG data is reconciled with robust IMU signals using a deep learning model with dilated causal convolutions,
                ensuring real-time haptic feedback. A rigorous filtering protocol ensures data quality:
              </p>
              <ul className="list-disc list-inside text-gray-300 mb-6 pl-4">
                <li><span className="font-semibold text-teal-300">High-pass Filter:</span> 70 Hz to eliminate motion artifacts.</li>
                <li><span className="font-semibold text-teal-300">Band-pass Filter:</span> 20 Hz to 300 Hz for physiologically relevant EMG components.</li>
                <li><span className="font-semibold text-teal-300">Notch Filter:</span> 48-52 Hz to suppress power line interference.</li>
              </ul>
              <DataChart
                title="Simulated sEMG Signal (Filtered)"
                data={MOCK_EMG_DATA}
                dataKey="value"
                unit="mV"
                color="#8884d8"
              />
            </Card>
          </section>

          <section id="machine-telemetry" ref={(el) => (sectionRefs.current['machine-telemetry'] = el)}>
            <SectionTitle
              id="machine-telemetry"
              title="Tattoo Machine Telemetry"
              subtitle="Capturing the Mechanical Signature of Artistic Tools"
            />
            <Card className="mb-12">
              <p className="text-gray-300 leading-relaxed mb-6">
                Understanding Lough's tools is crucial for his revitalization. The LOUGH hub captures telemetry from both coil
                and rotary machines, documenting variables like voltage, torque, RPM, and duty cycle.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3">Coil Machine Dynamics</h3>
              <p className="text-gray-300 leading-relaxed mb-4">
                Coil machines offer a "punchy" stroke. LOUGH monitors electromagnetic current, duty cycle (e.g., 55% for harder hit),
                and the "snap" of the needle. Example: Vlad Blad Infinite Liner Pro.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3">Rotary Machine and Brushless Motor Telemetry</h3>
              <p className="text-gray-300 leading-relaxed mb-6">
                Rotary pen machines (e.g., Vlad Blad Ultron 3 Max) provide smooth, continuous motion. Telemetry includes torque
                (g·cm) and RPM (up to 8500), ideal for shading with less mechanical feedback.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                <DataChart
                  title="Simulated Rotary Machine RPM"
                  data={MOCK_MACHINE_RPM_DATA}
                  dataKey="value"
                  unit="RPM"
                  color="#a0c4ff"
                />
                <DataChart
                  title="Simulated Coil Machine Voltage"
                  data={MOCK_MACHINE_VOLTAGE_DATA}
                  dataKey="value"
                  unit="V"
                  color="#ff7f50"
                />
              </div>

              <div className="overflow-x-auto">
                <table className="min-w-full bg-gray-800 rounded-lg shadow-md border border-gray-700">
                  <thead>
                    <tr className="bg-gray-700 text-teal-300 uppercase text-sm leading-normal">
                      <th className="py-3 px-6 text-left">Feature</th>
                      <th className="py-3 px-6 text-left">Coil Machine</th>
                      <th className="py-3 px-6 text-left">Rotary Pen</th>
                    </tr>
                  </thead>
                  <tbody className="text-gray-300 text-sm font-light">
                    {MACHINE_SPECS.map((spec, index) => (
                      <tr key={index} className="border-b border-gray-600 hover:bg-gray-700">
                        <td className="py-3 px-6 text-left whitespace-nowrap font-medium text-white">{spec.feature}</td>
                        <td className="py-3 px-6 text-left">{spec.coilMachine}</td>
                        <td className="py-3 px-6 text-left">{spec.rotaryPen}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </section>

          <section id="white-paper-engine" ref={(el) => (sectionRefs.current['white-paper-engine'] = el)}>
            <SectionTitle
              id="white-paper-engine"
              title='"White Paper" Engine'
              subtitle="Data Synthesis and Documentation for Industrial Standards"
            />
            <VideoDataOverlay /> {/* This component includes context for this section */}
            <Card className="mt-8">
              <p className="text-gray-300 leading-relaxed mb-6">
                The LOUGH architecture's "Data-Intensive White Paper" requirement is met by an engine converting raw bio-kinetic
                telemetry into structured technical reports. This leverages conversational AI to handle complex medical and technical
                nuances, favoring a Full Training Pipeline (FTP) for high-stakes accuracy.
              </p>
              <p className="text-gray-300 leading-relaxed">
                Integration with healthcare IT (e.g., EHRs) ensures scientific validity of skin-trauma data and healing-rate metrics.
                The "Dual-Machine" configuration (light tones vs. dark contrasts for sculptural depth) is meticulously documented.
              </p>
            </Card>
          </section>

          <section id="haptic-guidance" ref={(el) => (sectionRefs.current['haptic-guidance'] = el)}>
            <SectionTitle
              id="haptic-guidance"
              title="Haptic Guidance and Skill Transfer"
              subtitle="The Revitalization Protocol for Lancy Lough's Legacy"
            />
            <HapticFeedbackSimulator /> {/* This component covers this section's concepts */}
            <Card className="mt-8">
              <p className="text-gray-300 leading-relaxed mb-6">
                Lancy Lough’s legacy is operationalized through a haptic feedback framework, enabling user-adaptive training
                by detecting performance deficiencies in near real-time. Devices like the PHANTOM Omni provide force feedback
                based on the artist’s historically recorded positions.
              </p>
              <h3 className="text-xl font-semibold text-white mb-3">Training Regimen</h3>
              <p className="text-gray-300 leading-relaxed">
                The system provides "Intrinsic Feedback" (sensory stimulation from the simulator) and "Augmented Feedback"
                (a total score based on technique). For example, depth-dependent vibrotactile cues guide needle insertion
                depth. A "3-day training regimen" focuses on proprioceptive and haptic cues to internalize the "Loughian" technique.
              </p>
            </Card>
          </section>

          <section id="multimodal-ai" ref={(el) => (sectionRefs.current['multimodal-ai'] = el)}>
            <SectionTitle
              id="multimodal-ai"
              title="Multimodal AI and Transformer Architectures"
              subtitle="The Intelligence Core of LOUGH"
            />
            <Card className="mb-12">
              <p className="text-gray-300 leading-relaxed mb-6">
                The intelligence core of LOUGH is built upon Multimodal Transformers, processing entire sequences of diverse data
                (images, audio, time series) simultaneously to discern significant patterns. This is crucial for handling complex
                inputs like machine buzz, biometrics, and visual streams.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3">Multi-Task Learning and Zero-Shot Adaptation</h3>
              <p className="text-gray-300 leading-relaxed mb-4">
                A multi-task learning framework enhances generalization by recognizing motion intentions from fused sEMG and
                kinematic data. "Zero-Shot" models allow dynamic specification of artistic labels (e.g., "fine line," "soft shade")
                without additional training. For surgical-grade precision, a multimodal skill classification framework integrates:
              </p>
              <ul className="list-disc list-inside text-gray-300 mb-6 pl-4">
                <li><span className="font-semibold text-teal-300">3D CNN:</span> Processes video for gestures and hand positions.</li>
                <li><span className="font-semibold text-teal-300">1D CNN/LSTM:</span> Processes biometric and machine telemetry.</li>
                <li><span className="font-semibold text-teal-300">Class Activation Map (CAM):</span> Provides explainability for AI decisions, clarifying "Legacy Overlay" suggestions.</li>
              </ul>
              <p className="text-gray-300 leading-relaxed">
                The hub achieves real-time performance of approximately 1.1ms to 1.3ms for processing a 1-second input window,
                ensuring the "Legacy Overlay" remains responsive to the artist's current physical state.
              </p>
            </Card>
          </section>

          <section id="robotic-revitalization" ref={(el) => (sectionRefs.current['robotic-revitalization'] = el)}>
            <SectionTitle
              id="robotic-revitalization"
              title="Robotic Revitalization and the Autonomous Layer"
              subtitle="A New Format of Professional Presence"
            />
            <Card className="mb-12">
              <p className="text-gray-300 leading-relaxed mb-6">
                The "Autonomous Revitalization" module leverages technology akin to the Blackdot system, using scanners, algorithms,
                and microscopic dots (0.25mm) for surgical precision. This opens a new format of professional presence for Lancy Lough.
              </p>

              <h3 className="text-xl font-semibold text-white mb-3">Precision and Pain Mitigation</h3>
              <p className="text-gray-300 leading-relaxed mb-4">
                By targeting the precise junction between the epidermis and dermis, the system optimizes depth of penetration,
                reducing tattooing pain to a 0-2/10 on the pain scale. The "Lough" archive includes digital blueprints (e.g.,
                .tattoo file format) guiding robotic arms for 1:1 replicas of original artwork.
              </p>
              <p className="text-gray-300 leading-relaxed italic">
                This autonomous layer also functions as a "Virtual Guest Spot," allowing remote artist participation via video
                while a robotic device tattoos the client, preserving personal connection across distances.
              </p>
              <img src="https://picsum.photos/800/400?random=1" alt="Robotic Arm Tattooing" className="mt-8 rounded-lg shadow-lg" />
              <p className="text-gray-500 text-sm mt-2 text-center">Simulated robotic tattooing with precision</p>
            </Card>
          </section>

          <section id="socio-technical-integrity" ref={(el) => (sectionRefs.current['socio-technical-integrity'] = el)}>
            <SectionTitle
              id="socio-technical-integrity"
              title="Socio-Technical Integrity and the Lough Legacy"
              subtitle="Ethical Frameworks for a Living Digital Repository"
            />
            <Card className="mb-12">
              <p className="text-gray-300 leading-relaxed mb-6">
                Lancy Lough's legacy extends beyond technique to "Tattooing as Liberation Work" and "Trauma-Informed Client Care."
                The LOUGH architecture embeds ethical frameworks emphasizing:
              </p>
              <ul className="list-disc list-inside text-gray-300 mb-6 pl-4">
                <li><span className="font-semibold text-teal-300">Consent and Positive Value:</span> Ensuring data acquisition and revitalization prioritize well-being.</li>
                <li><span className="font-semibold text-teal-300">Transparency and Harm-Risk Mitigation:</span> Preventing tissue overworking and ensuring optimal healing via telemetry.</li>
                <li><span className="font-semibold text-teal-300">Inclusive Dialects:</span> Adopting AI models that respect community dialects and cultural nuances in tattooing.</li>
              </ul>
              <p className="text-gray-300 leading-relaxed italic">
                The architecture itself favors non-repetitive, sculpture-like forms, reflecting a commitment to variety and character
                essential to true art, avoiding the "literally repeating building designs" of standard automation.
              </p>
              <img src="https://picsum.photos/800/400?random=2" alt="Ethical AI Concept" className="mt-8 rounded-lg shadow-lg" />
              <p className="text-gray-500 text-sm mt-2 text-center">Conceptual art representing ethical considerations in AI</p>
            </Card>
          </section>

          <section id="conclusion" ref={(el) => (sectionRefs.current['conclusion'] = el)}>
            <SectionTitle
              id="conclusion"
              title="Conclusion: The Integrated Legacy Overlay"
              subtitle="Bridging Past, Present, and Future of Tattoo Science and Artistry"
            />
            <Card className="mb-12">
              <p className="text-lg leading-relaxed text-gray-200">
                The Legacy Overlay Unified Graphics Hub (LOUGH) architecture establishes a complete, high-fidelity ecosystem
                for preserving and revitalizing master-level artistry. By balancing extreme technical sensory monitoring with
                data-intensive documentation, LOUGH ensures that Lancy Lough's legacy is not a static archive, but a living,
                breathable professional entity.
              </p>
              <p className="mt-4 text-gray-300">
                Through hybrid sensor fusion, multimodal transformers, and haptic guidance, the Hub provides the computational
                infrastructure to bridge the past, present, and future of tattoo science and artistry. The result is a system
                that satisfies the "Gollum-style" requirement for extreme technical fidelity while maintaining the humanistic
                and personal core of the artist's professional identity.
              </p>
            </Card>
          </section>

        </div>
      </main>

      <ChatInterface />
    </div>
  );
};

export default App;
