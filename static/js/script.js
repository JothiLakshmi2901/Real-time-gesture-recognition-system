// const video = document.getElementById("video");
// const recognizedWordsContainer = document.getElementById("recognizedWords");
// const sentenceBox = document.getElementById("sentenceBox");
// const predictionBubble = document.getElementById("predictionBubble");
// const modeBanner = document.getElementById("modeBanner");

// const introOverlay = document.getElementById("introOverlay");
// const introScreen1 = document.getElementById("introScreen1");
// const introScreen2 = document.getElementById("introScreen2");
// const countdown1 = document.getElementById("countdown1");
// const countdown2 = document.getElementById("countdown2");
// const mainApp = document.getElementById("mainApp");

// const canvas = document.createElement("canvas");
// const ctx = canvas.getContext("2d");

// let stream = null;
// let detectionInterval = null;
// let lastProcessedTime = 0;
// const PROCESS_INTERVAL = 1000;

// let currentMode = "waiting";
// let instructionInterval = null;
// let pauseInstructionUntil = 0;
// let lastSpokenActionId = "";
// let backendTtsPlaying = false;
// let appStarted = false;

// window.addEventListener("load", async () => {
//     setPredictionBubble("No Hand");
//     renderRecognizedWords([]);
//     renderSentence("");
//     updateModeBanner("waiting");

//     await runIntroSequence();
// });

// async function runIntroSequence() {
//     await runCountdown(countdown1, "Starting instruction screen in", 10);

//     introScreen1.classList.remove("active");
//     introScreen2.classList.add("active");

//     await runCountdown(countdown2, "Starting detection screen in", 10);

//     introOverlay.style.display = "none";
//     mainApp.classList.add("active");

//     await startMainApplication();
// }

// function runCountdown(element, label, seconds) {
//     return new Promise(resolve => {
//         let remaining = seconds;
//         element.textContent = `${label} ${remaining} seconds`;

//         const timer = setInterval(() => {
//             remaining -= 1;

//             if (remaining > 0) {
//                 element.textContent = `${label} ${remaining} seconds`;
//             } else {
//                 clearInterval(timer);
//                 resolve();
//             }
//         }, 1000);
//     });
// }

// async function startMainApplication() {
//     if (appStarted) return;
//     appStarted = true;

//     await clearAllWords();
//     await startCamera();
//     startInstructionLoop();

//     setTimeout(() => {
//         speakLocal("Give start gesture to detect word", true);
//     }, 1200);
// }

// async function clearAllWords() {
//     try {
//         await fetch("/clear_words", { method: "POST" });
//     } catch (error) {
//         console.error("Clear error:", error);
//     }
// }

// async function startCamera() {
//     try {
//         if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
//             alert("Browser does not support camera access");
//             return;
//         }

//         stream = await navigator.mediaDevices.getUserMedia({
//             video: {
//                 width: { ideal: 640 },
//                 height: { ideal: 480 },
//                 facingMode: "user"
//             },
//             audio: false
//         });

//         video.srcObject = stream;

//         video.onloadedmetadata = async () => {
//             await video.play();
//             startDetection();
//         };

//         console.log("Camera started successfully");
//     } catch (error) {
//         console.error("Camera start error:", error);
//         if (error.name === "NotAllowedError") {
//             alert("Camera permission denied. Please allow camera access in your browser settings.");
//         } else if (error.name === "NotFoundError") {
//             alert("No camera found on this device.");
//         } else {
//             alert("Camera error: " + error.message);
//         }
//     }
// }

// function startDetection() {
//     if (detectionInterval) {
//         clearInterval(detectionInterval);
//     }
//     detectionInterval = setInterval(captureAndPredict, PROCESS_INTERVAL);
// }

// function captureAndPredict() {
//     if (!video.srcObject || video.readyState !== 4) return;

//     const now = Date.now();
//     if (now - lastProcessedTime < PROCESS_INTERVAL) return;
//     lastProcessedTime = now;

//     canvas.width = video.videoWidth;
//     canvas.height = video.videoHeight;

//     ctx.save();
//     ctx.clearRect(0, 0, canvas.width, canvas.height);
//     ctx.translate(canvas.width, 0);
//     ctx.scale(-1, 1);
//     ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
//     ctx.restore();

//     const imageData = canvas.toDataURL("image/jpeg", 0.8);

//     fetch("/process_frame", {
//         method: "POST",
//         headers: {
//             "Content-Type": "application/json"
//         },
//         body: JSON.stringify({ image: imageData })
//     })
//         .then(res => res.json())
//         .then(data => {
//             if (!data.success) {
//                 setPredictionBubble("No Hand");
//                 return;
//             }

//             backendTtsPlaying = data.tts_playing || false;

//             updatePredictionBubbleFromResponse(data);
//             updateDialogue(data.all_words || [], data.sentence || "");
//             handleModeChange(data.app_mode || "waiting");
//             handleActionVoice(data);
//         })
//         .catch(err => {
//             console.error("Prediction error:", err);
//             setPredictionBubble("No Hand");
//         });
// }

// function updatePredictionBubbleFromResponse(data) {
//     const handDetected = data.hand_detected;
//     const gestureRecognized = data.gesture_recognized;
//     const currentGesture = data.current_word || "";

//     if (!handDetected) {
//         setPredictionBubble("No Hand");
//     } else if (handDetected && !gestureRecognized) {
//         setPredictionBubble("No Gesture");
//     } else if (handDetected && gestureRecognized && currentGesture.trim() !== "") {
//         setPredictionBubble(formatGestureLabel(currentGesture));
//     } else {
//         setPredictionBubble("No Gesture");
//     }
// }

// function updateDialogue(words, sentence) {
//     renderRecognizedWords(words);
//     renderSentence(sentence);
// }

// function renderRecognizedWords(words) {
//     recognizedWordsContainer.innerHTML = "";

//     if (!words || words.length === 0) {
//         recognizedWordsContainer.innerHTML = `<span class="empty-text">No words recognized yet</span>`;
//         return;
//     }

//     words.forEach(word => {
//         const bubble = document.createElement("span");
//         bubble.className = "word-chip";
//         bubble.textContent = word;
//         recognizedWordsContainer.appendChild(bubble);
//     });
// }

// function renderSentence(sentence) {
//     if (!sentence || sentence.trim() === "") {
//         sentenceBox.textContent = "No sentence formed yet";
//         return;
//     }

//     sentenceBox.textContent = sentence;
// }

// function setPredictionBubble(text) {
//     predictionBubble.textContent = text;

//     if (text === "No Hand" || text === "No Gesture") {
//         predictionBubble.classList.add("empty");
//     } else {
//         predictionBubble.classList.remove("empty");
//     }
// }

// function formatGestureLabel(word) {
//     if (!word) return "";
//     return word
//         .replaceAll("_", " ")
//         .split(" ")
//         .map(part => part.charAt(0).toUpperCase() + part.slice(1))
//         .join(" ");
// }

// function updateModeBanner(mode) {
//     if (mode === "listening") {
//         modeBanner.textContent = "Listening mode: give your gestures";
//     } else if (mode === "stopped") {
//         modeBanner.textContent = "Prediction stopped: give speak command";
//     } else {
//         modeBanner.textContent = "Waiting for start gesture";
//     }
// }

// function handleModeChange(newMode) {
//     if (!newMode) return;

//     if (newMode !== currentMode) {
//         currentMode = newMode;
//         updateModeBanner(currentMode);

//         if (backendTtsPlaying) return;

//         if (currentMode === "listening") {
//             speakLocal("Now you can give gesture", true);
//             pauseInstructionUntil = Date.now() + 3000;
//         } else if (currentMode === "stopped") {
//             speechSynthesis.cancel();
//             speakLocal("Give speak command to voice", true);
//             pauseInstructionUntil = Date.now() + 3000;
//         } else {
//             speakLocal("Give start gesture to detect word", true);
//             pauseInstructionUntil = Date.now() + 3000;
//         }
//     } else {
//         updateModeBanner(currentMode);
//     }
// }

// function startInstructionLoop() {
//     if (instructionInterval) {
//         clearInterval(instructionInterval);
//     }

//     instructionInterval = setInterval(() => {
//         if (Date.now() < pauseInstructionUntil) return;
//         if (speechSynthesis.speaking) return;
//         if (backendTtsPlaying) return;

//         if (currentMode === "waiting") {
//             speakLocal("Give start gesture to detect word", false);
//         } else if (currentMode === "listening") {
//             speakLocal("Now you can give gesture", false);
//         } else if (currentMode === "stopped") {
//             speakLocal("Give speak command to voice", false);
//         }
//     }, 6000);
// }

// function handleActionVoice(data) {
//     const action = data.action || "none";
//     const word = data.word || "";
//     const sentence = data.sentence || "";

//     const actionId = `${action}|${word}|${sentence}`;

//     if (action === "none" || action === "waiting_for_start" || action === "waiting_for_speak") return;
//     if (actionId === lastSpokenActionId) return;

//     lastSpokenActionId = actionId;

//     if (action === "started") {
//         if (!backendTtsPlaying) {
//             speechSynthesis.cancel();
//             speakLocal("Now you can give gesture", true);
//         }
//         pauseInstructionUntil = Date.now() + 3000;
//         return;
//     }

//     if (action === "stopped") {
//         if (!backendTtsPlaying) {
//             speechSynthesis.cancel();
//             speakLocal("Give speak command to voice", true);
//         }
//         pauseInstructionUntil = Date.now() + 3000;
//         return;
//     }

//     if (action === "word_added" && word) {
//         if (!backendTtsPlaying) {
//             speakLocal(word, true);
//         }
//         pauseInstructionUntil = Date.now() + 2000;
//         return;
//     }

//     if (action === "backspace") {
//         if (!backendTtsPlaying) {
//             speakLocal("Deleted last word", true);
//         }
//         pauseInstructionUntil = Date.now() + 2000;
//         return;
//     }

//     if (action === "empty_sentence") {
//         if (!backendTtsPlaying) {
//             speakLocal("No sentence available", true);
//         }
//         pauseInstructionUntil = Date.now() + 2500;
//         return;
//     }

//     if (action === "sentence_spoken") {
//         speechSynthesis.cancel();
//         pauseInstructionUntil = Date.now() + 1000;
//         return;
//     }
// }

// function speakLocal(text, interrupt = false) {
//     if (!("speechSynthesis" in window)) return;
//     if (!text || !text.trim()) return;

//     if (interrupt) {
//         speechSynthesis.cancel();
//     } else if (speechSynthesis.speaking) {
//         return;
//     }

//     const utterance = new SpeechSynthesisUtterance(text);
//     utterance.rate = 0.95;
//     utterance.pitch = 1;
//     utterance.volume = 1;
//     speechSynthesis.speak(utterance);
// }

// window.addEventListener("beforeunload", () => {
//     if (detectionInterval) {
//         clearInterval(detectionInterval);
//     }

//     if (instructionInterval) {
//         clearInterval(instructionInterval);
//     }

//     speechSynthesis.cancel();

//     if (stream) {
//         stream.getTracks().forEach(track => track.stop());
//     }
// });

const video = document.getElementById("video");
const recognizedWordsContainer = document.getElementById("recognizedWords");
const sentenceBox = document.getElementById("sentenceBox");
const predictionBubble = document.getElementById("predictionBubble");
const modeBanner = document.getElementById("modeBanner");
const cameraStatusOverlay = document.getElementById("cameraStatusOverlay");

const introOverlay = document.getElementById("introOverlay");
const introScreen1 = document.getElementById("introScreen1");
const introScreen2 = document.getElementById("introScreen2");
const countdown1 = document.getElementById("countdown1");
const countdown2 = document.getElementById("countdown2");
const mainApp = document.getElementById("mainApp");

const canvas = document.createElement("canvas");
const ctx = canvas.getContext("2d");

let stream = null;
let detectionInterval = null;
let lastProcessedTime = 0;
const PROCESS_INTERVAL = 1000;

let currentMode = "waiting";
let instructionInterval = null;
let pauseInstructionUntil = 0;
let lastSpokenActionId = "";
let backendTtsPlaying = false;
let appStarted = false;

window.addEventListener("load", () => {
    setPredictionBubble("No Hand");
    renderRecognizedWords([]);
    renderSentence("");

    // The HTML inline script handles the intro countdown and sets mainApp active.
    // We poll here and start the camera as soon as mainApp becomes visible.
    waitForMainApp();
});

function waitForMainApp() {
    const check = setInterval(() => {
        if (mainApp.classList.contains("active")) {
            clearInterval(check);
            startMainApplication();
        }
    }, 200);
}

async function startMainApplication() {
    if (appStarted) return;
    appStarted = true;

    await clearAllWords();
    await startCamera();
    startInstructionLoop();

    setTimeout(() => {
        speakLocal("Give start gesture to detect word", true);
    }, 1200);
}

async function clearAllWords() {
    try {
        await fetch("/clear_words", { method: "POST" });
    } catch (error) {
        console.error("Clear error:", error);
    }
}

// ─────────────────────────────────────────────────────────
// startCamera — robust laptop webcam connection
// ─────────────────────────────────────────────────────────
async function startCamera() {
    if (cameraStatusOverlay) {
        cameraStatusOverlay.innerHTML = "🔄 Connecting to camera...";
    }

    try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            showCameraError("Browser does not support camera. Please use Chrome or Edge.");
            return;
        }

        // STEP 1: Trigger permission prompt with broad constraints
        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: "user"
            },
            audio: false
        });

        console.log("✅ Camera permission granted");

        // STEP 2: Enumerate cameras now that permission is granted
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(d => d.kind === "videoinput");
        console.log("📷 Cameras found:", videoDevices.map(d => d.label));

        // STEP 3: Find the built-in / integrated laptop webcam
        const builtIn = videoDevices.find(d => {
            const lbl = (d.label || "").toLowerCase();
            return (
                lbl.includes("integrated") ||
                lbl.includes("built-in") ||
                lbl.includes("internal") ||
                lbl.includes("webcam") ||
                lbl.includes("hd camera") ||
                lbl.includes("facetime") ||
                lbl.includes("front") ||
                lbl.includes("laptop")
            );
        });

        const targetCam = builtIn || videoDevices[0];
        const currentDeviceId = stream.getVideoTracks()[0]?.getSettings()?.deviceId;

        // STEP 4: Switch to the preferred camera if needed
        if (targetCam && currentDeviceId && targetCam.deviceId !== currentDeviceId) {
            stream.getTracks().forEach(t => t.stop());
            stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    deviceId: { exact: targetCam.deviceId },
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                },
                audio: false
            });
            console.log("🔄 Switched to:", targetCam.label);
        } else {
            console.log("✅ Using:", stream.getVideoTracks()[0]?.label || "unknown");
        }

        // STEP 5: Attach stream to <video>
        video.srcObject = stream;
        video.muted = true;
        video.playsInline = true;

        // STEP 6: Wait for video to be ready, then play
        await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new Error("Video load timeout"));
            }, 8000);

            video.onloadedmetadata = async () => {
                clearTimeout(timeout);
                try {
                    await video.play();
                    console.log("✅ Video playing:", video.videoWidth + "x" + video.videoHeight);
                    resolve();
                } catch (e) {
                    reject(e);
                }
            };

            // If metadata already available
            if (video.readyState >= 2) {
                clearTimeout(timeout);
                video.play().then(resolve).catch(reject);
            }
        });

        startDetection();

        if (cameraStatusOverlay) {
            cameraStatusOverlay.innerHTML = "🟡 Waiting for start gesture | 👋 No hand detected";
        }

    } catch (error) {
        console.error("❌ Camera error:", error.name, error.message);

        if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
            showCameraError("⛔ Camera blocked. Click the 🔒 lock icon in the address bar → allow Camera → refresh page.");
        } else if (error.name === "NotFoundError" || error.name === "DevicesNotFoundError") {
            showCameraError("📷 No camera found. Check if your webcam is plugged in.");
        } else if (error.name === "NotReadableError" || error.name === "TrackStartError") {
            showCameraError("🔒 Camera used by another app (Zoom/Teams). Close it and refresh.");
        } else if (error.name === "OverconstrainedError" || (error.message && error.message.includes("timeout"))) {
            console.warn("⚠️ Retrying with minimal constraints...");
            await startCameraFallback();
        } else {
            showCameraError("❌ " + error.message + " — Please refresh and allow camera.");
        }
    }
}

// Last-resort fallback: no constraints at all
async function startCameraFallback() {
    try {
        if (stream) stream.getTracks().forEach(t => t.stop());
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        video.srcObject = stream;
        video.muted = true;
        await video.play();
        console.log("✅ Fallback camera working");
        startDetection();
        if (cameraStatusOverlay) {
            cameraStatusOverlay.innerHTML = "🟡 Waiting for start gesture | 👋 No hand detected";
        }
    } catch (err) {
        showCameraError("❌ Cannot access any camera. Allow permission and refresh.");
    }
}

function showCameraError(msg) {
    console.error(msg);
    if (cameraStatusOverlay) {
        cameraStatusOverlay.innerHTML = msg;
        cameraStatusOverlay.style.fontSize = "11px";
        cameraStatusOverlay.style.padding = "14px 10px";
    }
}
// ─────────────────────────────────────────────────────────

function startDetection() {
    if (detectionInterval) clearInterval(detectionInterval);
    detectionInterval = setInterval(captureAndPredict, PROCESS_INTERVAL);
}

function captureAndPredict() {
    if (!video.srcObject) return;
    if (video.readyState < 2) return;
    if (video.videoWidth === 0 || video.videoHeight === 0) return;

    const now = Date.now();
    if (now - lastProcessedTime < PROCESS_INTERVAL) return;
    lastProcessedTime = now;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    ctx.save();
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    ctx.restore();

    const imageData = canvas.toDataURL("image/jpeg", 0.8);

    fetch("/process_frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: imageData })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            setPredictionBubble("No Hand");
            return;
        }

        backendTtsPlaying = data.tts_playing || false;

        updatePredictionBubbleFromResponse(data);
        updateDialogue(data.all_words || [], data.sentence || "");
        handleModeChange(data.app_mode || "waiting");
        handleActionVoice(data);
        updateStatusOverlay(data);
    })
    .catch(err => {
        console.error("Prediction error:", err);
        setPredictionBubble("No Hand");
    });
}

function updateStatusOverlay(data) {
    if (!cameraStatusOverlay) return;

    const hand = data.hand_detected;
    const gesture = data.current_word || "";
    const mode = data.app_mode || "waiting";

    let modeText = "🟡 Waiting for start gesture";
    if (mode === "listening") modeText = "🟢 Listening — give your gestures";
    else if (mode === "stopped") modeText = "🔴 Stopped — give speak command";

    const handText = hand
        ? (gesture ? `✋ Detected: ${formatGestureLabel(gesture)}` : "✋ Hand detected")
        : "👋 No hand detected";

    cameraStatusOverlay.innerHTML = `${modeText} | ${handText}`;
}

function updatePredictionBubbleFromResponse(data) {
    const handDetected = data.hand_detected;
    const gestureRecognized = data.gesture_recognized;
    const currentGesture = data.current_word || "";

    if (!handDetected) {
        setPredictionBubble("No Hand");
    } else if (!gestureRecognized) {
        setPredictionBubble("No Gesture");
    } else if (currentGesture.trim() !== "") {
        setPredictionBubble(formatGestureLabel(currentGesture));
    } else {
        setPredictionBubble("No Gesture");
    }
}

function updateDialogue(words, sentence) {
    renderRecognizedWords(words);
    renderSentence(sentence);
}

function renderRecognizedWords(words) {
    recognizedWordsContainer.innerHTML = "";
    if (!words || words.length === 0) {
        recognizedWordsContainer.innerHTML = `<span class="empty-text">No words recognized yet</span>`;
        return;
    }
    words.forEach(word => {
        const bubble = document.createElement("span");
        bubble.className = "word-chip";
        bubble.textContent = word;
        recognizedWordsContainer.appendChild(bubble);
    });
}

function renderSentence(sentence) {
    if (!sentence || sentence.trim() === "") {
        sentenceBox.textContent = "No sentence formed yet";
        return;
    }
    sentenceBox.textContent = sentence;
}

function setPredictionBubble(text) {
    predictionBubble.textContent = text;
    if (text === "No Hand" || text === "No Gesture") {
        predictionBubble.classList.add("empty");
    } else {
        predictionBubble.classList.remove("empty");
    }
}

function formatGestureLabel(word) {
    if (!word) return "";
    return word
        .replaceAll("_", " ")
        .split(" ")
        .map(part => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
}

function updateModeBanner(mode) {
    if (!modeBanner) return;
    if (mode === "listening") {
        modeBanner.textContent = "Listening mode: give your gestures";
    } else if (mode === "stopped") {
        modeBanner.textContent = "Prediction stopped: give speak command";
    } else {
        modeBanner.textContent = "Waiting for start gesture";
    }
}

function handleModeChange(newMode) {
    if (!newMode) return;

    if (newMode !== currentMode) {
        currentMode = newMode;
        updateModeBanner(currentMode);

        if (backendTtsPlaying) return;

        if (currentMode === "listening") {
            speakLocal("Now you can give gesture", true);
            pauseInstructionUntil = Date.now() + 3000;
        } else if (currentMode === "stopped") {
            speechSynthesis.cancel();
            speakLocal("Give speak command to voice", true);
            pauseInstructionUntil = Date.now() + 3000;
        } else {
            speakLocal("Give start gesture to detect word", true);
            pauseInstructionUntil = Date.now() + 3000;
        }
    } else {
        updateModeBanner(currentMode);
    }
}

function startInstructionLoop() {
    if (instructionInterval) clearInterval(instructionInterval);

    instructionInterval = setInterval(() => {
        if (Date.now() < pauseInstructionUntil) return;
        if (speechSynthesis.speaking) return;
        if (backendTtsPlaying) return;

        if (currentMode === "waiting") {
            speakLocal("Give start gesture to detect word", false);
        } else if (currentMode === "listening") {
            speakLocal("Now you can give gesture", false);
        } else if (currentMode === "stopped") {
            speakLocal("Give speak command to voice", false);
        }
    }, 6000);
}

function handleActionVoice(data) {
    const action = data.action || "none";
    const word = data.word || "";
    const sentence = data.sentence || "";
    const actionId = `${action}|${word}|${sentence}`;

    if (action === "none" || action === "waiting_for_start" || action === "waiting_for_speak") return;
    if (actionId === lastSpokenActionId) return;
    lastSpokenActionId = actionId;

    if (action === "started") {
        if (!backendTtsPlaying) { speechSynthesis.cancel(); speakLocal("Now you can give gesture", true); }
        pauseInstructionUntil = Date.now() + 3000;
        return;
    }
    if (action === "stopped") {
        if (!backendTtsPlaying) { speechSynthesis.cancel(); speakLocal("Give speak command to voice", true); }
        pauseInstructionUntil = Date.now() + 3000;
        return;
    }
    if (action === "word_added" && word) {
        if (!backendTtsPlaying) speakLocal(word, true);
        pauseInstructionUntil = Date.now() + 2000;
        return;
    }
    if (action === "backspace") {
        if (!backendTtsPlaying) speakLocal("Deleted last word", true);
        pauseInstructionUntil = Date.now() + 2000;
        return;
    }
    if (action === "empty_sentence") {
        if (!backendTtsPlaying) speakLocal("No sentence available", true);
        pauseInstructionUntil = Date.now() + 2500;
        return;
    }
    if (action === "sentence_spoken") {
        speechSynthesis.cancel();
        pauseInstructionUntil = Date.now() + 1000;
        return;
    }
}

function speakLocal(text, interrupt = false) {
    if (!("speechSynthesis" in window)) return;
    if (!text || !text.trim()) return;
    if (interrupt) {
        speechSynthesis.cancel();
    } else if (speechSynthesis.speaking) {
        return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1;
    utterance.volume = 1;
    speechSynthesis.speak(utterance);
}

window.addEventListener("beforeunload", () => {
    if (detectionInterval) clearInterval(detectionInterval);
    if (instructionInterval) clearInterval(instructionInterval);
    speechSynthesis.cancel();
    if (stream) stream.getTracks().forEach(track => track.stop());
});