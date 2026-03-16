# FieldFix AI: Project Story

## Inspiration
It all started with a simple realization: **I wanted to fix things using AI abilities**. When something breaks, whether it's an appliance at home or complex industrial equipment in the field, we usually have to stop what we're doing, wash our hands, and start digging through dense, hundreds-of-pages-long PDF manuals. 

I realized that field technicians face this problem on a massive scale. They are often stressed, working with their hands, and dealing with unreliable connectivity. They don't have time to type queries into a chatbot. They need a system that can *see* what they see, *hear* them out, and guide them step-by-step—hands-free. This inspired **FieldFix AI**: a real-time, interruptible AI assistant grounded in actual equipment manuals.

## What it does
FieldFix AI is a real-time AI assistant built specifically for field technicians. Technicians point their phone camera at a broken device and describe the problem by voice. The AI immediately sees the equipment, diagnoses the issue, and provides live, expert guidance. 

Crucially, every piece of advice is grounded in the actual equipment manual through section citations, delivered out loud. The system learns from every resolved case to build an institutional memory, and it forces a step-by-step workflow: the AI provides exactly one repair action at a time and waits for confirmation. Most importantly, it is fully interruptible—if the AI is moving too fast or explaining the wrong thing, the technician can cut it off mid-sentence to steer the conversation.

## How we built it
FieldFix AI is built around a robust **hub-and-spoke architecture** optimized for challenging mobile field environments. 

**The Frontend:** I built a Progressive Web App (PWA) using React, TypeScript, and Tailwind CSS. A PWA was crucial because it works cross-platform (iOS and Android) without requiring app store approval, making it accessible from just a URL. State management is efficiently handled by Zustand to keep the bundle small and reactive.

**The Communication Layer:** Mobile networks on a cell tower or satellite link treat multiple connections as competition, so I engineered a **single multiplexed WebSocket**. This single connection carries both binary PCM audio from the microphone and JSON control messages (like base64 camera frames)—minimizing overhead and connection drops.

**The Backend & AI:** 
The core is a FastAPI WebSocket handler running statelessly on Google Cloud Run. I integrated the **Gemini 2.5 Flash Live API** using the Google Agent Development Kit (ADK). This enables natural, bidirectional conversational interaction. 

To ensure the AI is reliable and doesn't hallucinate repair steps, the agent utilizes structured tool calling:
*   `diagnose_frame`: Uses Gemini Vision to analyze camera frames.
*   `search_manual`: Performs Retrieval-Augmented Generation (RAG) over manual chunks stored in Google Cloud Storage.
*   `lookup_similar_cases` & `save_resolved_case`: Reads and writes to Firestore to build out an institutional memory based on past repairs.

## Challenges we ran into
**The "Barge-In" (Interruption) Problem:**
In real life conversations, people cut each other off. If the AI is explaining step 3 but the technician is still stuck on step 2, they need to interrupt it immediately. Solving this was tough. I built a two-layer approach: the frontend calculates the Root Mean Square (RMS) energy of the audio buffer to quickly detect when the user starts speaking and sends a `barge_in` event over the WebSocket, while Gemini's built-in Automatic Activity Detection handles server-side fallback.

**Efficient RAG without a Vector Database:**
I wanted semantic search for the equipment manuals but without the complexity and cost of managing a dedicated Vector Database right out of the gate. For manuals that split into 100-500 chunks, I implemented an in-memory similarity search using NumPy. 

The mathematical similarity between the search query embedding vector $Q$ and the manual chunk embedding vector $C$ is calculated natively using Cosine Similarity:

$$ \text{Similarity}(Q, C) = \cos(\theta) = \frac{Q \cdot C}{\|Q\| \|C\|} = \frac{\sum_{i=1}^{n} Q_i C_i}{\sqrt{\sum_{i=1}^{n} Q_i^2} \sqrt{\sum_{i=1}^{n} C_i^2}} $$

Because the vectors are relatively small ($n=768$), this mathematical operation takes under a millisecond in NumPy. This approach scales horizontally by nature: each Cloud Run instance loads its own cache, requiring zero shared state.

## Accomplishments that we're proud of
I am incredibly proud of achieving true **multimodal interruptibility**. Getting a system to seamlessly handle streaming binary audio, process base64 video frames, execute structured backend tooling, and still be able to stop on a dime when a user interrupts it, is a complex orchestration challenge. 

I'm also proud of the **strict constraint mechanism** built into the ADK system prompt. By forcing the AI to successfully complete a `search_manual` tool call *before* it is ever allowed to dispense repair advice, the system effectively neutralizes dangerous hallucinations in high-stakes repair environments.

## What we learned
*   **Multimodal integration is challenging but rewarding:** Syncing audio processing, video frame extraction, and structured JSON data over a single connection pushed my understanding of real-time web protocols.
*   **Agent Orchestration:** Using the Google ADK taught me how to constrain an LLM effectively. Building tools that act as "guardrails" is fundamentally different from building standard API endpoints.
*   **Designing for Humans:** I learned that an AI tool for the field isn't about giving the smartest answer immediately; it's about pacing. Giving the user *one step at a time* and waiting for confirmation creates a drastically better user experience than dumping a 10-step list on them.

## What's next for Field Fix AI
The MVP proves the value of grounded, multimodal AI for repairs, but there are clear paths to scale:
1.  **Vector Database Integration:** Transitioning from the NumPy in-memory approach to Vertex AI Vector Search to scale to thousands of manuals across different equipment lines.
2.  **Smarter Institutional Memory:** Upgrading the Firestore search logic from simple keyword matching to embedding-based similarity to match past fixes based heavily on semantic symptoms.
3.  **Enterprise Integrations:** Integrating the WebSocket backend with standard enterprise IAM and syncing repair resolutions back into traditional ticketing systems like Jira or ServiceNow.

## Built with
Gemini 2.5 Flash Live API, Google Agent Development Kit (ADK), Python, FastAPI, WebSockets, React, TypeScript, Tailwind CSS, Zustand, Vite (PWA), Google Cloud Run, Google Cloud Storage, Firestore, Terraform, NumPy
