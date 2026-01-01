let socket;
let audioContext;
let processor;
let microphone;
const recordBtn = document.getElementById('recordBtn');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const chatBox = document.getElementById('chatBox');
const canvas = document.getElementById('visualizer');
const canvasCtx = canvas.getContext('2d');

// Initialize WebSocket
function initWebSocket() {
    // If hosted on a server, we use the current host and the correct protocol
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    console.log("Connecting to WebSocket:", wsUrl);
    
    socket = new WebSocket(wsUrl);
    socket.binaryType = 'arraybuffer';

    socket.onopen = () => {
        statusDot.classList.add('status-connected');
        statusText.innerText = 'Connecté';
    };

    socket.onclose = () => {
        statusDot.classList.remove('status-connected');
        statusText.innerText = 'Déconnecté';
        setTimeout(initWebSocket, 2000);
    };

    socket.onmessage = async (event) => {
        if (typeof event.data === 'string') {
            const data = JSON.parse(event.data);
            handleTextMessage(data);
        } else {
            // It's binary audio data (PCM float32 24000Hz from XTTS)
            playAudioBuffer(event.data);
        }
    };
}

function handleTextMessage(data) {
    const div = document.createElement('div');
    div.className = 'msg ' + (data.type === 'transcription' ? 'user-msg' : 'ai-msg');
    div.innerText = (data.type === 'transcription' ? 'Vous: ' : 'IA: ') + data.text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Audio Playback
let nextStartTime = 0;
function playAudioBuffer(arrayBuffer) {
    if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    // The backend sends float32 PCM at 24000Hz (XTTS default)
    const float32Data = new Float32Array(arrayBuffer);
    const audioBuffer = audioContext.createBuffer(1, float32Data.length, 24000);
    audioBuffer.getChannelData(0).set(float32Data);

    const source = audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(audioContext.destination);

    // Precise scheduling for gapless playback
    const currentTime = audioContext.currentTime;
    if (nextStartTime < currentTime) {
        nextStartTime = currentTime;
    }
    source.start(nextStartTime);
    nextStartTime += audioBuffer.duration;
}

// Audio Recording
async function startRecording() {
    if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)();
    if (audioContext.state === 'suspended') {
        await audioContext.resume();
    }
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        microphone = audioContext.createMediaStreamSource(stream);
        
        // We need 16000Hz for Whisper usually. 
        // We'll use a ScriptProcessor (deprecated but simple for prototype) 
        // or AudioWorklet for better performance.
        processor = audioContext.createScriptProcessor(4096, 1, 1);
        
        microphone.connect(processor);
        processor.connect(audioContext.destination);

        processor.onaudioprocess = (e) => {
            if (socket && socket.readyState === WebSocket.OPEN) {
                const inputData = e.inputBuffer.getChannelData(0);
                // Downsample to 16kHz if needed, here we just convert to Int16
                const int16Data = convertFloat32ToInt16(inputData);
                socket.send(int16Data.buffer);
            }
            visualize(e.inputBuffer.getChannelData(0));
        };
        
        recordBtn.classList.replace('btn-primary', 'btn-danger');
    } catch (err) {
        console.error('Error accessing microphone:', err);
    }
}

function stopRecording() {
    if (processor) {
        processor.disconnect();
        microphone.disconnect();
    }
    recordBtn.classList.replace('btn-danger', 'btn-primary');
}

function convertFloat32ToInt16(buffer) {
    let l = buffer.length;
    let buf = new Int16Array(l);
    while (l--) {
        buf[l] = Math.min(1, buffer[l]) * 0x7FFF;
    }
    return buf;
}

// Visualizer
function visualize(data) {
    canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
    canvasCtx.fillStyle = '#4caf50';
    const barWidth = (canvas.width / data.length) * 2.5;
    let x = 0;
    for (let i = 0; i < data.length; i++) {
        const barHeight = Math.abs(data[i]) * canvas.height * 2;
        canvasCtx.fillRect(x, canvas.height / 2 - barHeight / 2, barWidth, barHeight);
        x += barWidth + 1;
    }
}

recordBtn.onmousedown = startRecording;
recordBtn.onmouseup = stopRecording;
recordBtn.ontouchstart = (e) => { e.preventDefault(); startRecording(); };
recordBtn.ontouchend = (e) => { e.preventDefault(); stopRecording(); };

initWebSocket();
