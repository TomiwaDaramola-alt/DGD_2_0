

/**
 * DGD 2.0 — DGD CONSULT AU
 * Self-Injecting AI Chat Widget Engine
 * Location: static/js/brain.js
 */

window.addEventListener('DOMContentLoaded', () => {
    console.log("🧠 DGD Brain Script Detected & Running!");

    // 1. Core Rule-Based Data Engine
    const knowledgeBase = [
        {
            keywords: ["hello", "hi", "hey", "greetings"],
            reply: "Hello! Welcome to DGD CONSULT AU. How can I help you with your Australian migration journey today?"
        },
        {
            keywords: ["student", "study", "subclass 500", "university", "course"],
            reply: "For an Australian Student Visa (Subclass 500), you need a Confirmation of Enrolment (CoE), English tests (IELTS/PTE), and proof of financial capacity. Our intake handling fee is 100,000 NGN via Paystack."
        },
        {
            keywords: ["partner", "marriage", "spouse", "subclass 820", "de facto"],
            reply: "Partner Visas (Subclass 820/309) allow spouses or de facto partners of Australian citizens/PRs to live in Australia. You must provide extensive evidence of a shared life."
        },
        {
            keywords: ["cost", "price", "fee", "paystack", "how much"],
            reply: "Our transparent processing fees are: Initial Consultation is Complimentary. Student Visa Intake is 100,000 NGN. Partner Visa Intake is 250,000 NGN. Paid securely via Paystack."
        },
        {
            keywords: ["login", "portal", "account", "dashboard"],
            reply: "Clients can log in using their Username/Email. Staff can log in directly using their unique Employee ID (e.g., DGD-AU-001)."
        }
    ];

    // 2. Inject CSS Styles directly into the document head
    const styleNode = document.createElement('style');
    styleNode.innerHTML = `
        .dgd-ai-wrapper { position: fixed; bottom: 20px; right: 20px; z-index: 99999; font-family: system-ui, -apple-system, sans-serif; }
        .dgd-ai-ball { width: 60px; height: 60px; border-radius: 30px; background: #2563eb; color: white; display: flex; align-items: center; justify-content: center; font-size: 26px; cursor: pointer; box-shadow: 0 4px 12px rgba(37,99,235,0.4); transition: transform 0.2s; }
        .dgd-ai-ball:hover { transform: scale(1.05); }
        .dgd-ai-panel { width: 340px; height: 440px; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 8px 32px rgba(0,0,0,0.15); display: none; flex-direction: column; position: absolute; bottom: 75px; right: 0; overflow: hidden; }
        .dgd-ai-head { background: #0f172a; color: white; padding: 14px; display: flex; justify-content: space-between; font-weight: 600; font-size: 14px; }
        .dgd-ai-body { flex: 1; padding: 14px; overflow-y: auto; background: #f8fafc; display: flex; flex-direction: column; gap: 10px; }
        .dgd-bubble { max-width: 85%; padding: 8px 12px; font-size: 13.5px; border-radius: 10px; line-height: 1.4; word-wrap: break-word; }
        .dgd-bubble.bot { background: white; color: #1e293b; align-self: flex-start; border: 1px solid #e2e8f0; }
        .dgd-bubble.user { background: #2563eb; color: white; align-self: flex-end; }
        .dgd-ai-foot { padding: 10px; background: white; border-top: 1px solid #e2e8f0; display: flex; gap: 6px; }
        .dgd-ai-foot input { flex: 1; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; outline: none; font-size: 13.5px; }
        .dgd-ai-foot button { background: #2563eb; color: white; border: none; padding: 0 14px; border-radius: 6px; cursor: pointer; font-size: 13.5px; font-weight: 500; }
    `;
    document.head.appendChild(styleNode);

    // 3. Construct Structural DOM nodes explicitly
    const uiContainer = document.createElement('div');
    uiContainer.className = 'dgd-ai-wrapper';
    uiContainer.innerHTML = `
        <div class="dgd-ai-panel" id="dgdUiPanel">
            <div class="dgd-ai-head">
                <span>🌏 DGD Assistant</span>
                <span style="cursor:pointer;" id="dgdUiClose">✕</span>
            </div>
            <div class="dgd-ai-body" id="dgdUiBody">
                <div class="dgd-bubble bot">Hello! Ask me any sentence about visas, registration costs, or portal system access.</div>
            </div>
            <div class="dgd-ai-foot">
                <input type="text" id="dgdUiInput" placeholder="Type a message..." autocomplete="off">
                <button id="dgdUiSend">Send</button>
            </div>
        </div>
        <div class="dgd-ai-ball" id="dgdUiBall">💬</div>
    `;
    document.body.appendChild(uiContainer);

    // 4. Element Selectors & Observers
    const ball = document.getElementById('dgdUiBall');
    const panel = document.getElementById('dgdUiPanel');
    const closeBtn = document.getElementById('dgdUiClose');
    const sendBtn = document.getElementById('dgdUiSend');
    const inputField = document.getElementById('dgdUiInput');
    const body = document.getElementById('dgdUiBody');

    ball.addEventListener('click', () => {
        panel.style.display = (panel.style.display === 'flex') ? 'none' : 'flex';
        if(panel.style.display === 'flex') inputField.focus();
    });
    
    closeBtn.addEventListener('click', () => { panel.style.display = 'none'; });

    const runChatLogic = () => {
        const text = inputField.value.trim();
        if(!text) return;

        // Render User Message
        const uDiv = document.createElement('div');
        uDiv.className = 'dgd-bubble user';
        uDiv.innerText = text;
        body.appendChild(uDiv);
        inputField.value = '';
        body.scrollTop = body.scrollHeight;

        // Process Match Response
        setTimeout(() => {
            const cleanText = text.toLowerCase();
            let matchedReply = "I'm here to guide you on Australian migration paths. Could you specify if your inquiry regards a Student Visa, Partner Visa, or processing Fees?";
            
            for (const entry of knowledgeBase) {
                if (entry.keywords.some(k => cleanText.includes(k))) {
                    matchedReply = entry.reply;
                    break;
                }
            }

            const bDiv = document.createElement('div');
            bDiv.className = 'dgd-bubble bot';
            bDiv.innerText = matchedReply;
            body.appendChild(bDiv);
            body.scrollTop = body.scrollHeight;
        }, 500);
    };

    sendBtn.addEventListener('click', runChatLogic);
    inputField.addEventListener('keypress', (e) => { if(e.key === 'Enter') runChatLogic(); });
});
