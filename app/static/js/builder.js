/**
 * ETERNALS TERMINAL ENGINE v1.0
 * Architect: Eternals Dev
 * Description: Frontend Logic for Secure Mail Node
 */

// =============================================================================
// 1. CONFIGURATION & STATE
// =============================================================================
const API_URL = "/api";
let SESSION_TOKEN = null;
let CURRENT_USER = null;
let DEVICE_ID = localStorage.getItem("eternals_did");

// Generate Persistent Device ID (Browser Fingerprint)
if (!DEVICE_ID) {
    DEVICE_ID = 'dev-' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
    localStorage.setItem("eternals_did", DEVICE_ID);
}

// DOM Elements
const outputDiv = document.getElementById('output');
const inputLine = document.getElementById('input-line');
const cmdInput = document.getElementById('cmd-input');
const promptSpan = document.getElementById('prompt');

// App State Machine
let APP_STATE = "BOOT"; // BOOT, LANDING, INTERVIEW, LOGIN, REGISTER, DASHBOARD

// =============================================================================
// 2. UTILITY FUNCTIONS (UI)
// =============================================================================

function print(text, className="log-entry") {
    const div = document.createElement('div');
    div.className = className;
    div.innerHTML = text; 
    outputDiv.appendChild(div);
    scrollToBottom();
}

async function typeWriter(text, className="log-entry", speed=15) {
    const div = document.createElement('div');
    div.className = className;
    outputDiv.appendChild(div);
    
    let i = 0;
    while (i < text.length) {
        div.innerHTML += text.charAt(i);
        i++;
        scrollToBottom();
        // Variasi kecepatan biar natural seperti hacker ngetik
        await new Promise(r => setTimeout(r, speed + Math.random() * 10));
    }
}

function scrollToBottom() {
    const term = document.getElementById('terminal');
    if(term) term.scrollTop = term.scrollHeight;
}

function clearScreen() {
    outputDiv.innerHTML = "";
}

function enableInput() {
    inputLine.style.display = "flex";
    cmdInput.value = "";
    cmdInput.focus();
}

function disableInput() {
    inputLine.style.display = "none";
}

// Helper untuk Request yang butuh Login (Secured Routes)
function getAuthHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + SESSION_TOKEN
    };
}

// =============================================================================
// 3. CORE SEQUENCES
// =============================================================================

// --- A. BOOT SEQUENCE ---
async function bootSequence() {
    await typeWriter("Initializing Eternals Core Kernel...", "system-msg");
    await new Promise(r => setTimeout(r, 300));
    print("[OK] Loading Crypto Modules...");
    print("[OK] Establishing Secure Handshake...");
    print("[OK] Verifying Signature: Eternals Dev"); 
    print(`[OK] Device Identity: ${DEVICE_ID}`);
    await new Promise(r => setTimeout(r, 600));
    
    clearScreen();
    showLanding();
}

// --- B. LANDING PAGE ---
function showLanding() {
    APP_STATE = "LANDING";
    
    // ASCII ART DARI KAMU (Escaped backticks)
    const logo = `
    <pre style="color:#33ff33; font-weight:bold; line-height:1.1; font-size: 10px;">
      ..      .          s                                                            ..    .x+=:.   
   x88f\` \`..x88. .>     :8                                                      x .d88"    z\`    ^%  
 :8888   xf\`*8888%     .88                  .u    .      u.    u.                5888R        .   <k 
:8888f .888  \`"\`      :888ooo      .u     .d88B :@8c   x@88k u@88c.       u      '888R      .@8Ned8" 
88888' X8888. >"8x  -*8888888   ud8888.  ="8888f8888r ^"8888""8888"    us888u.    888R    .@^%8888"  
88888  ?88888< 888>   8888    :888'8888.   4888>'88"    8888  888R  .@88 "8888"   888R   x88:  \`)8b. 
88888   "88888 "8%    8888    d888 '88%"   4888> '      8888  888R  9888  9888    888R   8888N=*8888 
88888 '  \`8888>       8888    8888.+"      4888>        8888  888R  9888  9888    888R    %8"    R88 
\`8888> %  X88!       .8888Lu= 8888L       .d888L .+     8888  888R  9888  9888    888R     @8Wou 9%  
 \`888X  \`~""\`   :    ^%888* '8888c. .+  ^"8888*"     "*88*" 8888" 9888  9888   .888B . .888888P\`   
   "88k.      .~       'Y"     "88888%       "Y"         ""   'Y"   "888*""888"  ^*888%  \`   ^"F     
     \`""*==~~\`                   "YP'                                ^Y"   ^Y'     "%

    :: ETERNALS MAIL NODE :: Encrypted & Anonymous ::
    [ Architect: Eternals Dev ]
    </pre>
    `;
    print(logo);
    print("Initializing Secure Environment...", "system-msg");
    print("Zero-Knowledge Protocol: ACTIVE", "ai-msg");
    print("<br>");
    
    const menuDiv = document.createElement("div");
    menuDiv.innerHTML = `
        <button class="btn-terminal" onclick="showLogin()">> ACCESS SYSTEM (LOGIN)</button>
        <button class="btn-terminal" style="margin-left:10px;" onclick="startInterview()">> NEW IDENTITY (REGISTER)</button>
    `;
    outputDiv.appendChild(menuDiv);
    
    const credit = document.createElement("div");
    credit.style.marginTop = "20px";
    credit.style.fontSize = "10px";
    credit.style.color = "#444";
    credit.innerHTML = "© 2024 Eternals Network. Plausible Deniability Enabled.";
    outputDiv.appendChild(credit);
}

// --- C. INTERVIEW (AI PROXY) ---
async function startInterview() {
    clearScreen();
    APP_STATE = "INTERVIEW";
    print(":: ESTABLISHING SECURE CHANNEL ::", "system-msg");
    print("Connecting to The Guardian...", "log-entry");

    try {
        const res = await fetch(API_URL + "/init-session", {
            method: "POST", headers: {"Content-Type":"application/json"},
            body: JSON.stringify({ device_id: DEVICE_ID })
        });
        const data = await res.json();
        
        if (data.token) {
            SESSION_TOKEN = data.token;
            print("Connection Established.", "system-msg");
            print("GUARDIAN: Identify yourself. What is your purpose here?", "ai-msg");
            enableInput();
        } else {
            print("Handshake Error: " + data.error, "error-msg");
        }
    } catch (e) {
        print("Network Error: Server Unreachable.", "error-msg");
    }
}

// --- D. REGISTER FORM ---
function showRegister(payload) {
    clearScreen();
    APP_STATE = "REGISTER";
    print(":: ACCESS GRANTED ::", "system-msg");
    print("Guardian Approved. Create your credentials.");
    
    const container = document.createElement("div");
    container.className = "form-box";
    container.innerHTML = `
        <input id="reg-user" class="form-input" placeholder="Username (Login only)">
        <input id="reg-alias" class="form-input" placeholder="Alias (e.g. shadow01)">
        <input id="reg-pass" class="form-input" type="password" placeholder="Password">
        <button id="btn-create" class="btn-terminal">CREATE IDENTITY</button>
    `;
    outputDiv.appendChild(container);

    document.getElementById("btn-create").onclick = async () => {
        const user = document.getElementById("reg-user").value;
        const alias = document.getElementById("reg-alias").value;
        const pass = document.getElementById("reg-pass").value;

        if(!user || !alias || !pass) {
            print(">> Error: All fields required.", "error-msg");
            return;
        }
        
        print("Encrypting identity...", "log-entry");
        const res = await fetch(API_URL + "/create-account", {
            method: "POST", headers: {"Content-Type":"application/json"},
            body: JSON.stringify({
                sess: payload.sess, dev: payload.dev, sign: payload.sign,
                username: user, alias: alias, password: pass
            })
        });
        
        const data = await res.json();
        if (data.status === "CREATED") {
            print(">> Identity Created Successfully.", "system-msg");
            setTimeout(showLogin, 1500);
        } else {
            print(">> Creation Failed: " + data.error, "error-msg");
        }
    };
}

// --- E. LOGIN FORM ---
function showLogin() {
    clearScreen();
    APP_STATE = "LOGIN";
    print(":: SYSTEM AUTHENTICATION ::", "system-msg");

    const container = document.createElement("div");
    container.className = "form-box";
    container.innerHTML = `
        <input id="login-user" class="form-input" placeholder="Username">
        <input id="login-pass" class="form-input" type="password" placeholder="Password">
        <button id="btn-login" class="btn-terminal">AUTHENTICATE</button>
        <button onclick="showLanding()" class="btn-terminal" style="border-color:#555; color:#555">CANCEL</button>
    `;
    outputDiv.appendChild(container);

    document.getElementById("btn-login").onclick = async () => {
        const user = document.getElementById("login-user").value;
        const pass = document.getElementById("login-pass").value;
        
        print("Verifying credentials...", "log-entry");
        
        try {
            const res = await fetch(API_URL + "/login", {
                method: "POST", headers: {"Content-Type":"application/json"},
                body: JSON.stringify({ username: user, password: pass, device_id: DEVICE_ID })
            });
            const data = await res.json();
            
            if (data.status === "SUCCESS") {
                SESSION_TOKEN = data.token;
                CURRENT_USER = user;
                showDashboard(data.alias);
            } else {
                print(">> Access Denied: " + data.error, "error-msg");
            }
        } catch (e) {
            print(">> Connection Error.", "error-msg");
        }
    };
}

// =============================================================================
// 4. DASHBOARD & FEATURES
// =============================================================================

function showDashboard(alias) {
    clearScreen();
    APP_STATE = "DASHBOARD";
    
    print(`:: ETERNALS UPLINK :: USER: ${alias.toUpperCase()} ::`, "system-msg");
    print("Status: ENCRYPTED | Node: ACTIVE", "log-entry");
    print("---------------------------------------------------");
    
    const menuDiv = document.createElement("div");
    menuDiv.innerHTML = `
        <div style="margin-bottom: 10px;">
            <button class="btn-terminal" onclick="fetchInbox()">[1] INBOX STREAM</button>
            <button class="btn-terminal" onclick="showCompose()">[2] SEND (BRIDGE)</button>
        </div>
        <div>
            <button class="btn-terminal" onclick="showSettings()">[3] SETTINGS</button>
            <button class="btn-terminal" onclick="location.reload()" style="color:#ff5555; border-color:#ff5555">[4] TERMINATE</button>
        </div>
    `;
    outputDiv.appendChild(menuDiv);
    
    // Auto load inbox
    setTimeout(fetchInbox, 500);
}

// --- FEATURE 1: INBOX ---
async function fetchInbox() {
    // Hapus list lama jika ada
    const old = document.getElementById("mail-list");
    if(old) old.remove();

    print("Fetching encrypted packets...", "log-entry");
    
    try {
        // [IMPORTANT] Pakai Header Authorization
        const res = await fetch(API_URL + "/inbox", {
            method: "POST", headers: getAuthHeaders(),
            body: JSON.stringify({ username: CURRENT_USER })
        });
        
        // Handle Session Expired
        if (res.status === 401) {
            print(">> Session Expired. Re-login required.", "error-msg");
            setTimeout(showLogin, 2000);
            return;
        }

        const mails = await res.json();
        
        const listContainer = document.createElement("div");
        listContainer.id = "mail-list";
        listContainer.style.marginTop = "20px";
        
        if(mails.length === 0) {
            print(">> Inbox is empty or purged.", "log-entry");
            return;
        }

        mails.forEach(mail => {
            const row = document.createElement("div");
            row.className = "log-entry";
            row.style.borderBottom = "1px dashed #333";
            row.style.padding = "8px 0";
            row.style.cursor = "pointer";
            row.style.transition = "all 0.2s";
            
            // Highlight effect
            row.onmouseover = () => row.style.background = "#111";
            row.onmouseout = () => row.style.background = "transparent";
            
            const time = new Date(mail.time).toLocaleTimeString();
            row.innerHTML = `<span style="color:#666">[${time}]</span> <span style="color:#fff; font-weight:bold">${mail.from}</span> <br> >> ${mail.subject}`;
            row.onclick = () => readMail(mail);
            
            listContainer.appendChild(row);
        });
        
        outputDiv.appendChild(listContainer);
        print(`>> ${mails.length} Messages Decrypted.`, "system-msg");
        scrollToBottom();

    } catch (e) {
        print(">> Decryption Error: " + e, "error-msg");
    }
}

function readMail(mail) {
    clearScreen();
    print(":: DECRYPTED MESSAGE ::", "system-msg");
    print(`FROM: ${mail.from}`);
    print(`TIME: ${new Date(mail.time).toLocaleString()}`);
    print(`SUBJ: ${mail.subject}`);
    print("---------------------------------------------------");
    print(mail.body, "ai-msg"); 
    print("---------------------------------------------------");
    
    const btn = document.createElement("button");
    btn.className = "btn-terminal";
    btn.innerText = "< RETURN TO DASHBOARD";
    btn.onclick = () => showDashboard(CURRENT_USER); 
    outputDiv.appendChild(btn);
}

// --- FEATURE 2: COMPOSE (SMTP) ---
function showCompose() {
    clearScreen();
    print(":: SMTP BRIDGE (OUTBOUND) ::", "system-msg");
    print("Note: Uses your own SMTP credentials. We do not log them.", "log-entry");
    
    const form = document.createElement("div");
    form.className = "form-box";
    form.innerHTML = `
        <div style="color:#888; margin-bottom:5px">-- TARGET --</div>
        <input id="mail-to" class="form-input" placeholder="To: target@example.com">
        <input id="mail-subj" class="form-input" placeholder="Subject">
        <textarea id="mail-body" class="form-input" rows="4" placeholder="Message Body..."></textarea>
        
        <div style="color:#888; margin-bottom:5px; margin-top:10px">-- BRIDGE CONFIG --</div>
        <input id="smtp-host" class="form-input" placeholder="Host (e.g. smtp.gmail.com)">
        <input id="smtp-user" class="form-input" placeholder="SMTP User">
        <input id="smtp-pass" class="form-input" type="password" placeholder="SMTP Password/App Password">
        
        <button id="btn-send" class="btn-terminal">EXECUTE SEND</button>
        <button onclick="showDashboard(CURRENT_USER)" class="btn-terminal" style="border-color:#555; color:#555">CANCEL</button>
    `;
    outputDiv.appendChild(form);

    document.getElementById("btn-send").onclick = async () => {
        const btn = document.getElementById("btn-send");
        btn.disabled = true;
        btn.innerText = "TRANSMITTING...";
        
        const payload = {
            to: document.getElementById("mail-to").value,
            subject: document.getElementById("mail-subj").value,
            message: document.getElementById("mail-body").value,
            smtp_host: document.getElementById("smtp-host").value,
            smtp_user: document.getElementById("smtp-user").value,
            smtp_pass: document.getElementById("smtp-pass").value
        };

        try {
            const res = await fetch(API_URL + "/send-bridge", {
                method: "POST", headers: getAuthHeaders(),
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            if (data.status === "SENT") {
                print(">> STATUS: DELIVERY CONFIRMED.", "system-msg");
                setTimeout(() => showDashboard(CURRENT_USER), 2000);
            } else {
                print(">> ERROR: " + data.error, "error-msg");
                btn.disabled = false;
                btn.innerText = "RETRY";
            }
        } catch (e) {
            print(">> Bridge Error.", "error-msg");
            btn.disabled = false;
        }
    };
}

// --- FEATURE 3: SETTINGS (WEBHOOK) ---
function showSettings() {
    clearScreen();
    print(":: NODE CONFIGURATION ::", "system-msg");
    print("Configure Auto-Forwarding Webhook (JSON POST).");
    
    const form = document.createElement("div");
    form.className = "form-box";
    form.innerHTML = `
        <div style="color:#888; margin-bottom:5px">-- WEBHOOK URL --</div>
        <input id="conf-webhook" class="form-input" placeholder="https://your-api.com/callback">
        <div style="font-size:10px; color:#555; margin-bottom:10px;">
            * Emails will be forwarded here as encrypted JSON.
        </div>
        
        <button id="btn-save" class="btn-terminal">SAVE CONFIG</button>
        <button onclick="showDashboard(CURRENT_USER)" class="btn-terminal" style="border-color:#555; color:#555">BACK</button>
    `;
    outputDiv.appendChild(form);
    
    document.getElementById("btn-save").onclick = async () => {
        const url = document.getElementById("conf-webhook").value;
        const res = await fetch(API_URL + "/settings", {
            method: "POST", headers: getAuthHeaders(),
            body: JSON.stringify({ username: CURRENT_USER, webhook_url: url })
        });
        const data = await res.json();
        
        if (data.status === "UPDATED") {
            print(">> Configuration Updated.", "system-msg");
        } else {
            print(">> Error: " + data.error, "error-msg");
        }
    };
}

// =============================================================================
// 5. GLOBAL EVENT LISTENERS
// =============================================================================

// Handle Chat Input (Interview Mode)
cmdInput.addEventListener("keypress", async function(e) {
    if (e.key === "Enter") {
        const msg = cmdInput.value;
        if(!msg) return;
        
        cmdInput.value = "";
        
        if (APP_STATE === "INTERVIEW") {
            print("YOU: " + msg, "log-entry"); 
            disableInput();
            
            try {
                const res = await fetch(API_URL + "/chat-proxy", {
                    method: "POST", headers: {"Content-Type":"application/json"},
                    body: JSON.stringify({ token: SESSION_TOKEN, message: msg })
                });
                const data = await res.json();
                
                if (data.command === "REDIRECT") {
                    print("GUARDIAN: Access Granted.", "system-msg");
                    setTimeout(() => showRegister(data.payload), 1500);
                } else {
                    print("GUARDIAN: " + data.reply, "ai-msg");
                    enableInput();
                }
            } catch (e) {
                print(">> Connection Lost.", "error-msg");
                enableInput();
            }
        }
    }
});

// START
bootSequence();
