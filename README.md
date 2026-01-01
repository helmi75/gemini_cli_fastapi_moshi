# Real-Time Voice Assistant (Moshi Style)

Assistant vocal temps réel utilisant FastAPI, Whisper Turbo (STT), XTTS v2 (TTS) et Gemini 1.5 Flash (LLM) avec Grounding Vertex AI Search.

## 🚀 Fonctionnalités
- **STT :** Whisper Turbo (Local GPU) - Transcription ultra-rapide en Français.
- **LLM :** Gemini 1.5 Flash (Vertex AI) - Réponses concises avec recherche Google/Vertex Search.
- **TTS :** XTTS v2 (Local GPU) - Synthèse vocale fluide avec clonage de voix.
- **Interface :** Web minimaliste avec visualiseur audio et mode "Push-to-talk".

## 🛠️ Installation & Déploiement

### 1. Prérequis
- Un serveur avec GPU NVIDIA (ex: Vast.ai, RunPod) avec Docker & Docker Compose.
- Un projet Google Cloud avec l'API Vertex AI activée.
- Votre fichier de credentials Google Cloud : `secrets/key.json`.
- (Optionnel) Un fichier `static/reference.wav` (10-15s) pour la voix personnalisée.

### 2. Configuration
Modifiez le fichier `.env` avec vos informations :
```env
GOOGLE_CLOUD_PROJECT="votre-project-id"
VERTEX_DATA_STORE_ID="votre-datastore-id"
GOOGLE_APPLICATION_CREDENTIALS="/app/secrets/key.json"
COQUI_TOS_AGREED=1
```

### 3. Lancement (Vast.ai / Serveur GPU)
```bash
# Cloner le projet
git clone https://github.com/helmi75/gemini_cli_fastapi_moshi.git
cd gemini_cli_fastapi_moshi

# Placer les secrets
mkdir -p secrets
# Copiez votre key.json dans secrets/

# Lancer avec Docker
docker-compose up --build -d
```

*Note : Le premier lancement télécharge environ 10 Go de modèles. Utilisez `docker-compose logs -f` pour suivre la progression.*

## 🎤 Accès Micro & Sécurité (Important)
Sur un serveur distant (non-localhost), les navigateurs bloquent le microphone si vous n'êtes pas en HTTPS.

### Solution A : Autoriser l'IP dans Chrome (La plus rapide)
1. Copiez l'URL de votre serveur (ex: `http://123.45.67.89:8000`).
2. Allez sur : `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
3. Activez l'option, collez l'URL et relancez Chrome.

### Solution B : Tunnel HTTPS (La plus pro)
Utilisez `cloudflared` ou `ngrok` pour exposer votre port 8000 via une URL `https://`.

## 🧪 Tests
Après le lancement, vous pouvez vérifier le bon fonctionnement du WebSocket :
```bash
pip install pytest pytest-asyncio websockets numpy
pytest test_websocket.py
```

## 📂 Structure du Projet
- `main.py` : Serveur FastAPI & WebSocket.
- `audio_engine.py` : Logique STT (Whisper) et TTS (XTTS).
- `vertex_rag.py` : Connexion à Gemini et grounding Vertex AI Search.
- `static/` : Interface Frontend (HTML/JS).
