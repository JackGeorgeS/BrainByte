// --- GLOBAL ELEMENTS ---
const glow = document.querySelector('.cursor-glow');
const tooltip = document.getElementById('level-tooltip');
const terminal = document.getElementById('system-terminal');

let currentQuestions = [];
let currentQuestionIndex = 0;
let currentLevelReward = 0;
let mistake = 0;
let currentTierId = null;

// --- 1. MOUSE MOVEMENT (FIXED) ---
document.addEventListener('mousemove', (e) => {
    if (glow) {
        glow.style.left = e.pageX + 'px';
        glow.style.top = e.pageY + 'px';
    }
    if (tooltip && tooltip.style.display === 'block') {
        tooltip.style.left = (e.pageX + 15) + 'px';
        tooltip.style.top = (e.pageY + 15) + 'px';
    }
});

// --- 2. HOVER EFFECTS ---
document.addEventListener('mouseover', (e) => {
    const target = e.target.closest('.map-node, button, .si-buttons-scifi__style-5__button-2');
    if (!target) return;

    glow.classList.remove('hovering', 'hover-locked', 'hover-hud');

    if (target.classList.contains('map-node')) {
        const classList = Array.from(target.classList);
        const levelClass = classList.find(c => c.startsWith('level-'));
        const nodeLevelId = parseInt(levelClass.split('-')[1]);
        
        const originalXp = target.dataset.xp;

        document.getElementById('tooltip-name').innerText = target.dataset.name;
        document.getElementById('tooltip-subject').innerText = target.dataset.subject;
        document.getElementById('tooltip-difficulty').innerText = "Tier " + target.dataset.diff;
        
        if (USER_LEVEL > nodeLevelId) {
            document.getElementById('tooltip-xp').innerText = "25";
            document.getElementById('tooltip-xp').style.color = "#f196f1"; // Visual warning
        } else {
            document.getElementById('tooltip-xp').innerText = originalXp;
            document.getElementById('tooltip-xp').style.color = "#47b7d8"; // Standard cyan
        }
        tooltip.style.display = 'block';

        if (target.classList.contains('locked')) {
            glow.classList.add('hover-locked');
            tooltip.classList.add('locked-tooltip');
        } else {
            tooltip.classList.remove('locked-tooltip');
            glow.classList.add('hovering');
        }
    } else {
        glow.classList.add('hover-hud');
    }
});

document.addEventListener('mouseout', (e) => {
    if (e.target.closest('.map-node, button')) {
        tooltip.style.display = 'none';
        glow.classList.remove('hovering', 'hover-locked', 'hover-hud');
    }
});

// --- 3. LEVEL LOGIC ---
async function openLevel(levelId) {
    currentTierId = levelId;
    const node = document.querySelector(`.level-${levelId}`);
    
    if (node.classList.contains('locked')) {
        terminal.innerText = "ACCESS DENIED: LEVEL ENCRYPTED";
        terminal.style.display = 'block';
        terminal.classList.add('terminal-flicker');
        setTimeout(() => {
            terminal.style.display = 'none';
            terminal.classList.remove('terminal-flicker');
        }, 2000);
        return;
    }

    currentLevelReward = parseInt(node.dataset.xp);
    mistake = 0; // Reset mistakes for the new level attempt

    try {
        const res = await fetch(`/api/questions/${levelId}`);
        const data = await res.json();
        

        // Shuffle the 10 questions and take only 5
        currentQuestions = data.questions
            .sort(() => 0.5 - Math.random())
            .slice(0, 5);

        currentQuestionIndex = 0;
        document.getElementById('modal-level-title').innerText = data.level_name.toUpperCase();
        
        showQuestion();
        document.getElementById('quiz-overlay').style.display = 'flex';
    } catch (err) {
        console.error("Data fetch error:", err);
    }
}

function showQuestion() {
    const q = currentQuestions[currentQuestionIndex];
    document.getElementById('modal-question-text').innerText = q.text;
    const grid = document.getElementById('modal-answer-grid');
    grid.innerHTML = ''; 

    q.answers.forEach(ans => {
        grid.innerHTML += `
            <button class="si-buttons-scifi__style-3__button-1" onclick="submitAnswer(${ans.correct}, event)">
                <span>${ans.text}</span>
                <helper-1></helper-1><shine></shine><ripple></ripple>
            </button>`;
    });
}

async function submitAnswer(isCorrect, event) {
    const clickedButton = event.currentTarget;
    const allButtons = document.querySelectorAll('#modal-answer-grid button');
    const feedback = document.getElementById('quiz-feedback');

    allButtons.forEach(btn => btn.style.pointerEvents = 'none');

    if (isCorrect) {
        clickedButton.classList.add('btn-correct');
        feedback.innerText = "ACCESS GRANTED: CORRECT";
        feedback.className = "feedback-box feedback-success";

        currentQuestionIndex++;

        setTimeout(async () => {
            if (currentQuestionIndex < currentQuestions.length) {
                feedback.innerText = "";
                showQuestion(); 
            } else {
                // --- FINISHED LEVEL (CORRECT LAST ANSWER) ---
                await finishLevel();
            }
        }, 1200);
    } else {
        clickedButton.classList.add('btn-wrong');
        const q = currentQuestions[currentQuestionIndex];
        allButtons.forEach((btn, idx) => {
            if (q.answers[idx].correct) btn.classList.add('btn-correct');
        });

        if (mistake === 0) {
            feedback.innerText = "WARNING: 1 MISTAKE DETECTED - LAST CHANCE";
            feedback.className = "feedback-box feedback-error";
            mistake++;
            
            setTimeout(async () => {
                currentQuestionIndex++;
                if (currentQuestionIndex < currentQuestions.length) {
                    feedback.innerText = "";
                    showQuestion(); 
                } else {
                    // --- FINISHED LEVEL (MISTAKE ON LAST ANSWER) ---
                    // This was previously just location.reload()
                    await finishLevel();
                }
            }, 2000);
        } else {
            feedback.innerText = "CRITICAL ERROR: ACCESS DENIED";
            feedback.className = "feedback-box feedback-error";
            setTimeout(() => { 
                closeLevel(); 
                feedback.innerText = ""; 
            }, 2000);
        }
    }
}

// Helper function to handle the XP update and Level Up modal
async function finishLevel() {
    const feedback = document.getElementById('quiz-feedback');
    feedback.innerText = "UPLOADING DATA PACKET...";
    
    // 1. Send points and tier_id to the backend
    const res = await fetch('/update_xp', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ 
            points: currentLevelReward, 
            tier_id: currentTierId 
        })
    });
    const result = await res.json();

    // 2. Handle the response message (e.g., "Redundant data detected")
    if (result.status === "success") {
        // Show the user the actual points they earned (25 or full reward)
        feedback.innerText = `${result.message} (+${result.points_earned} XP)`;
        
        // 3. Short delay so they can read the message before the modal or reload
        await new Promise(resolve => setTimeout(resolve, 2000));

        if (result.level_up) {
            document.getElementById('new-level-display').innerText = result.new_level;
            document.getElementById('level-up-modal').style.display = 'flex';
        } else {
            location.reload(); 
        }
    }
}

function closeLevel() {
    document.getElementById('quiz-overlay').style.display = 'none';
}

function toggleQuestLog() {
    document.getElementById('quest-log').classList.toggle('active');
}

// Add to map.js
function toggleStudyModule() {
    const studyModule = document.getElementById('study-module');
    if (studyModule.style.display === 'none' || studyModule.style.display === '') {
        studyModule.style.display = 'flex';
    } else {
        studyModule.style.display = 'none';
    }
}


let currentStudyPage = 1;
const totalStudyPages = 3;
const studyTitles = {
    1: "SYSTEM BASICS",
    2: "LOGIC & OPERATORS",
    3: "DATA SEQUENCES"
};

// In map.js
function setStudyPage(pageNum) {
    const userLvl = USER_LEVEL; // Uses the global variable you already have in map.html
    
    // Check level requirements before switching
    if (pageNum === 2 && userLvl < 4) return denyAccess();
    if (pageNum === 3 && userLvl < 7) return denyAccess();
    if (pageNum < 1 || pageNum > totalStudyPages) return;

    document.querySelectorAll('.study-page').forEach(p => p.style.display = 'none');
    document.getElementById(`study-p${pageNum}`).style.display = 'block';
    
    document.querySelectorAll('.page-num').forEach((n, idx) => {
        n.classList.toggle('active', (idx + 1) === pageNum);
    });
    
    document.getElementById('study-page-title').innerText = studyTitles[pageNum];
    currentStudyPage = pageNum;
}

function denyAccess() {
    // Reuse your existing terminal flicker for feedback
    const terminal = document.getElementById('system-terminal');
    terminal.innerText = "ERROR: DATA ENCRYPTED - INSUFFICIENT CLEARANCE";
    terminal.style.display = 'block';
    terminal.classList.add('terminal-flicker');
    setTimeout(() => {
        terminal.style.display = 'none';
        terminal.classList.remove('terminal-flicker');
    }, 2000);
}

function changeStudyPage(direction) {
    const targetPage = currentStudyPage + direction;
    setStudyPage(targetPage);
}

const music = document.getElementById('bg-soundtrack');

    // 1. Start music on the first click anywhere (Browser requirement)
    document.addEventListener('click', () => {
        if (music && music.paused) {
            music.play().catch(err => console.log("Waiting for user interaction..."));
        }
    }, { once: true });

    // 2. Function to stop music when heading to the map
    function stopMusicAndPlay(url) {
        if (music) {
            music.pause();
            music.currentTime = 0; // Reset to start
        }
        window.location.href = url;
}

function toggleNewsModule() {
    const newsModule = document.getElementById('news-module');
    if (newsModule.style.display === 'none' || newsModule.style.display === '') {
        newsModule.style.display = 'flex';
    } else {
        newsModule.style.display = 'none';
    }
}

// Add to static/map.js

// 1. Function to toggle expansion
function toggleReadMore(btn) {
    const wrapper = btn.previousElementSibling;
    const isCollapsed = wrapper.classList.toggle('collapsed');
    btn.querySelector('span').innerText = isCollapsed ? 'Read More' : 'Read Less';
}

// 2. Initialize news items to check text length
document.addEventListener("DOMContentLoaded", function() {
    const newsItems = document.querySelectorAll('.news-item');
    
    newsItems.forEach(item => {
        const wrapper = item.querySelector('.news-content-wrapper');
        const btn = item.querySelector('.read-more-btn');
        
        // If text is long (scrollHeight > 65), show the button
        if (wrapper && wrapper.scrollHeight > 65) {
            btn.style.display = 'inline-flex';
        } else if (wrapper) {
            wrapper.classList.remove('collapsed'); // Remove fade if text is short
        }
    });
});

// 2. Initialize news items when the page loads
document.addEventListener("DOMContentLoaded", function() {
    const newsItems = document.querySelectorAll('.news-item');
    
    newsItems.forEach(item => {
        const wrapper = item.querySelector('.news-content-wrapper');
        const btn = item.querySelector('.read-more-btn');
        
        // If text is long, show the button
        if (wrapper && wrapper.scrollHeight > 65) {
            btn.style.display = 'inline-flex';
        } else if (wrapper) {
            wrapper.classList.remove('collapsed'); // Remove fade if text is short
        }
    });
});