let socket;
let audioContext;
let processor;
let microphone;
let isRecording = false;

const recordBtn = document.getElementById('recordBtn');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const chatBox = document.getElementById('chatBox');
const debugLog = document.getElementById('debugLog');

function log(msg) {
    console.log(msg);
    const line = document.createElement('div');
    line.innerText = `[${new Date().toLocaleTimeString()}] ${msg}`;
    debugLog.prepend(line);
}

function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    log(`Connexion WebSocket vers: ${wsUrl}`);
    
    socket = new WebSocket(wsUrl);
    socket.binaryType = 'arraybuffer';

    socket.onopen = () => {
        statusDot.className = 'status-dot status-connected';
        statusText.innerText = 'Connecté (Prêt)';
        log("WebSocket ouvert avec succès");
    };

    socket.onclose = (e) => {
        statusDot.className = 'status-dot';
        statusText.innerText = 'Déconnecté';
        log(`WebSocket fermé: ${e.code} ${e.reason}`);
        setTimeout(initWebSocket, 3000);
    };

    socket.onerror = (err) => {
        log(`Erreur WebSocket détectée`);
    };

    socket.onmessage = (event) => {
        if (typeof event.data === 'string') {
            const data = JSON.parse(event.data);
            handleTextMessage(data);
        } else {
            playAudioBuffer(event.data);
        }
    };
}

function handleTextMessage(data) {
    log(`Message reçu: ${data.type}`);
    const div = document.createElement('div');
    div.className = 'msg ' + (data.type === 'transcription' ? 'user-msg' : 'ai-msg');
    div.innerText = (data.type === 'transcription' ? 'Vous: ' : 'IA: ') + data.text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function playAudioBuffer(arrayBuffer) {
    if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const float32Data = new Float32Array(arrayBuffer);
    const audioBuffer = audioContext.createBuffer(1, float32Data.length, 24000);
    audioBuffer.getChannelData(0).set(float32Data);
    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);
    source.start();
}

async function startRecording() {
    log("Demande d'accès micro...");
    try {
        if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)();
        if (audioContext.state === 'suspended') await audioContext.resume();

        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        log("Micro accessible");
        
        microphone = audioContext.createMediaStreamSource(stream);
        processor = audioContext.createScriptProcessor(4096, 1, 1);
        
        microphone.connect(processor);
        processor.connect(audioContext.destination);

        processor.onaudioprocess = (e) => {
            if (socket && socket.readyState === WebSocket.OPEN) {
                const inputData = e.inputBuffer.getChannelData(0);
                const int16Data = new Int16Array(inputData.length);
                for (let i = 0; i < inputData.length; i++) {
                    int16Data[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
                }
                socket.send(int16Data.buffer);
            }
        };
        
        recordBtn.classList.replace('btn-primary', 'btn-danger');
        recordBtn.innerText = '⏹';
        isRecording = true;
        log("Enregistrement en cours...");
    } catch (err) {
        log(`ERREUR MICRO: ${err.message}`);
        alert(`Micro bloqué : ${err.message}. Vérifiez les permissions (icône cadenas).`);
    }
}

function stopRecording() {
    log("Arrêt de l'enregistrement");
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ "type": "end_of_speech" }));
    }
    if (processor) {
        processor.disconnect();
        microphone.disconnect();
    }
    recordBtn.classList.replace('btn-danger', 'btn-primary');
    recordBtn.innerText = '🎤';
    isRecording = false;
}

recordBtn.onclick = () => {
    log(`Clic bouton (isRecording=${isRecording})`);
    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
};

// Initialisation
initWebSocket();
