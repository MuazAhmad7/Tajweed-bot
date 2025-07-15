// Global variables for audio processing
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let ws = null;
let currentRecordingAyah = null;
let tooltipTimeout = null;
let currentReciter = 'mishary'; // Default reciter
let currentSurah = 1; // Default to Al-Fatiha

// Surah data
const surahData = {
    1: {
        name: "Al-Fatiha",
        arabicName: "الفاتحة",
        ayahs: [
            {
                arabic: "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
                translation: "In the Name of Allah—the Most Compassionate, Most Merciful.",
                transliteration: "Bismil laahir Rahmaanir Raheem",
                words: [
                    { text: "بِسْمِ", root: "بسم", trans: "In (the) name", translit: "bis'mi" },
                    { text: "ٱللَّهِ", root: "الله", trans: "(of) Allah", translit: "al-lahi", tajweed: "ghunnah" },
                    { text: "ٱلرَّحْمَٰنِ", root: "رحم", trans: "the Most Gracious", translit: "al-rahmani", tajweed: "ghunnah madd" },
                    { text: "ٱلرَّحِيمِ", root: "رحم", trans: "the Most Merciful", translit: "al-rahimi", tajweed: "ghunnah madd" }
                ]
            },
            {
                arabic: "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ",
                translation: "All praise is for Allah—Lord of all worlds",
                transliteration: "Alhamdu lillaahi Rabbil 'aalameen",
                words: [
                    { text: "ٱلْحَمْدُ", root: "حمد", trans: "All praises and thanks", translit: "al-hamdu", tajweed: "hamzat-wasl" },
                    { text: "لِلَّهِ", root: "الله", trans: "(be) to Allah", translit: "lillahi", tajweed: "ghunnah" },
                    { text: "رَبِّ", root: "ربب", trans: "the Lord", translit: "rabbi", tajweed: "ghunnah shaddah" },
                    { text: "ٱلْعَٰلَمِينَ", root: "علم", trans: "of the universe", translit: "al-'alamina", tajweed: "hamzat-wasl madd" }
                ]
            },
            {
                arabic: "ٱلرَّحْمَٰنِ ٱلرَّحِيمِ",
                translation: "the Most Compassionate, Most Merciful",
                transliteration: "Ar-Rahmaanir Raheem",
                words: [
                    { text: "ٱلرَّحْمَٰنِ", root: "رحم", trans: "The Most Gracious", translit: "al-rahmani", tajweed: "hamzat-wasl ghunnah shaddah madd" },
                    { text: "ٱلرَّحِيمِ", root: "رحم", trans: "the Most Merciful", translit: "al-rahimi", tajweed: "hamzat-wasl ghunnah shaddah madd" }
                ]
            },
            {
                arabic: "مَٰلِكِ يَوْمِ ٱلدِّينِ",
                translation: "Master of the Day of Judgment",
                transliteration: "Maaliki Yawmid Deen",
                words: [
                    { text: "مَٰلِكِ", root: "ملك", trans: "(The) Master", translit: "maliki", tajweed: "madd" },
                    { text: "يَوْمِ", root: "يوم", trans: "(of the) Day", translit: "yawmi" },
                    { text: "ٱلدِّينِ", root: "دين", trans: "(of the) Judgment", translit: "al-dini", tajweed: "hamzat-wasl ghunnah shaddah madd" }
                ]
            },
            {
                arabic: "إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ",
                translation: "You ˹alone˺ we worship and You ˹alone˺ we ask for help",
                transliteration: "iyyaaka na'budu wa-iyyaaka nasta'een",
                words: [
                    { text: "إِيَّاكَ", root: "ايا", trans: "You Alone", translit: "iyyaka", tajweed: "shaddah madd" },
                    { text: "نَعْبُدُ", root: "عبد", trans: "we worship", translit: "na'budu" },
                    { text: "وَإِيَّاكَ", root: "ايا", trans: "and You Alone", translit: "wa-iyyaka", tajweed: "shaddah madd" },
                    { text: "نَسْتَعِينُ", root: "عون", trans: "we ask for help", translit: "nasta'inu", tajweed: "madd" }
                ]
            },
            {
                arabic: "ٱهْدِنَا ٱلصِّرَٰطَ ٱلْمُسْتَقِيمَ",
                translation: "Guide us along the Straight Path",
                transliteration: "ihdinas Siraatal Mustaqeem",
                words: [
                    { text: "ٱهْدِنَا", root: "هدي", trans: "Guide us", translit: "ih'dina", tajweed: "hamzat-wasl" },
                    { text: "ٱلصِّرَٰطَ", root: "صرط", trans: "(to) the path", translit: "al-sirata", tajweed: "hamzat-wasl laam-shamsiyya tafkheem shaddah" },
                    { text: "ٱلْمُسْتَقِيمَ", root: "قوم", trans: "the straight", translit: "al-mus'taqima", tajweed: "hamzat-wasl madd" }
                ]
            },
            {
                arabic: "صِرَٰطَ ٱلَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ ٱلْمَغْضُوبِ عَلَيْهِمْ وَلَا ٱلضَّآلِّينَ",
                translation: "the Path of those You have blessed—not those You are displeased with, or those who are astray",
                transliteration: "Siraatal lazeena an'amta alaihim ghayril maghdoobi alaihim wa-lad daaalleen",
                words: [
                    { text: "صِرَٰطَ", root: "صرط", trans: "(The) path", translit: "sirata", tajweed: "tafkheem" },
                    { text: "ٱلَّذِينَ", root: "الذين", trans: "(of) those", translit: "alladhina", tajweed: "hamzat-wasl ghunnah shaddah madd" },
                    { text: "أَنْعَمْتَ", root: "نعم", trans: "You have bestowed (Your) Favors", translit: "an'amta", tajweed: "ithhar" },
                    { text: "عَلَيْهِمْ", root: "علي", trans: "on them", translit: "alayhim" },
                    { text: "غَيْرِ", root: "غير", trans: "not (of)", translit: "ghayri" },
                    { text: "ٱلْمَغْضُوبِ", root: "غضب", trans: "those who earned (Your) wrath", translit: "al-maghdubi", tajweed: "hamzat-wasl tafkheem" },
                    { text: "عَلَيْهِمْ", root: "علي", trans: "on themselves", translit: "alayhim" },
                    { text: "وَلَا", root: "لا", trans: "and not", translit: "wala" },
                    { text: "ٱلضَّآلِّينَ", root: "ضلل", trans: "(of) those who go astray", translit: "al-dalina", tajweed: "hamzat-wasl ghunnah shaddah madd" }
                ]
            }
        ]
    },
    113: {
        name: "Al-Falaq",
        arabicName: "الفلق",
        ayahs: [
            {
                arabic: "قُلْ أَعُوذُ بِرَبِّ ٱلْفَلَقِ",
                translation: "Say, ˹O Prophet,˺ \"I seek refuge in the Lord of the daybreak",
                transliteration: "Qul a'oodhu bi rabbil falaq",
                words: [
                    { text: "قُلْ", root: "قول", trans: "Say", translit: "qul", tajweed: "tafkheem" },
                    { text: "أَعُوذُ", root: "عوذ", trans: "I seek refuge", translit: "a'oodhu" },
                    { text: "بِرَبِّ", root: "ربب", trans: "in (the) Lord", translit: "bi-rabbi", tajweed: "shaddah" },
                    { text: "ٱلْفَلَقِ", root: "فلق", trans: "(of) the daybreak", translit: "al-falaq", tajweed: "hamzat-wasl qalqalah" }
                ]
            },
            {
                arabic: "مِن شَرِّ مَا خَلَقَ",
                translation: "from the evil of whatever He has created,",
                transliteration: "Min sharri maa khalaq",
                words: [
                    { text: "مِن", root: "من", trans: "From", translit: "min", tajweed: "ikhfa" },
                    { text: "شَرِّ", root: "شرر", trans: "(the) evil", translit: "sharri", tajweed: "shaddah" },
                    { text: "مَا", root: "ما", trans: "(of) what", translit: "maa", tajweed: "madd" },
                    { text: "خَلَقَ", root: "خلق", trans: "He created", translit: "khalaq", tajweed: "qalqalah" }
                ]
            },
            {
                arabic: "وَمِن شَرِّ غَاسِقٍ إِذَا وَقَبَ",
                translation: "and from the evil of the night when it grows dark,",
                transliteration: "Wa min sharri ghaasiqin idhaa waqab",
                words: [
                    { text: "وَمِن", root: "من", trans: "And from", translit: "wa-min", tajweed: "ikhfa" },
                    { text: "شَرِّ", root: "شرر", trans: "(the) evil", translit: "sharri", tajweed: "shaddah" },
                    { text: "غَاسِقٍ", root: "غسق", trans: "(of the) darkness", translit: "ghaasiqin", tajweed: "madd ithhar" },
                    { text: "إِذَا", root: "اذا", trans: "when", translit: "idhaa", tajweed: "madd" },
                    { text: "وَقَبَ", root: "وقب", trans: "it settles", translit: "waqab", tajweed: "qalqalah" }
                ]
            },
            {
                arabic: "وَمِن شَرِّ ٱلنَّفَّـٰثَـٰتِ فِى ٱلْعُقَدِ",
                translation: "and from the evil of those ˹witches˺ who blow on knots,",
                transliteration: "Wa min sharrin naffaathaati fil 'uqad",
                words: [
                    { text: "وَمِن", root: "من", trans: "And from", translit: "wa-min", tajweed: "ikhfa" },
                    { text: "شَرِّ", root: "شرر", trans: "(the) evil", translit: "sharri", tajweed: "shaddah" },
                    { text: "ٱلنَّفَّـٰثَـٰتِ", root: "نفث", trans: "(of) the blowers", translit: "an-naffaathaati", tajweed: "hamzat-wasl ghunnah shaddah madd" },
                    { text: "فِى", root: "في", trans: "in", translit: "fee", tajweed: "hamzat-wasl" },
                    { text: "ٱلْعُقَدِ", root: "عقد", trans: "the knots", translit: "al-'uqad", tajweed: "hamzat-wasl" }
                ]
            },
            {
                arabic: "وَمِن شَرِّ حَاسِدٍ إِذَا حَسَدَ",
                translation: "and from the evil of an envier when they envy.\"",
                transliteration: "Wa min sharri haasidin idhaa hasad",
                words: [
                    { text: "وَمِن", root: "من", trans: "And from", translit: "wa-min", tajweed: "ikhfa" },
                    { text: "شَرِّ", root: "شرر", trans: "(the) evil", translit: "sharri", tajweed: "shaddah" },
                    { text: "حَاسِدٍ", root: "حسد", trans: "(of) an envier", translit: "haasidin", tajweed: "madd ithhar" },
                    { text: "إِذَا", root: "اذا", trans: "when", translit: "idhaa", tajweed: "madd" },
                    { text: "حَسَدَ", root: "حسد", trans: "he envies", translit: "hasad", tajweed: "qalqalah" }
                ]
            }
        ]
    }
};

const processingMessages = [
    "Whispering your ayah to the neural net",
    "Decoding divine frequencies",
    "Hold on... we're ironing your ghunna",
    "Just making sure your qalqala didn't jump off the page",
    "Fixing your ikhfaa with duct tape"
];

// Theme handling function
function handleThemeChange(isDark) {
    // Update body attribute
    document.body.setAttribute('data-theme', isDark ? 'dark' : 'light');
    
    // Update theme in localStorage
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    
    // Update toggle buttons
    const themeToggle = document.getElementById('themeToggle');
    const mobileThemeToggle = document.getElementById('mobileThemeToggle');
    
    if (themeToggle) {
        themeToggle.textContent = isDark ? '☀️' : '🌙';
    }
    if (mobileThemeToggle) {
        mobileThemeToggle.textContent = isDark ? '☀️' : '🌙';
    }
    
    // Update renderer background if it exists (for landing page)
    if (typeof updateRendererBackground === 'function') {
        updateRendererBackground();
    }
    
    // Update colors if they exist (for landing page)
    if (typeof targetColor !== 'undefined' && typeof THREE !== 'undefined') {
        targetColor = new THREE.Color(isDark ? 0x1e88e5 : 0x42a5f5);
        if (typeof pointLight1 !== 'undefined' && typeof pointLight2 !== 'undefined') {
            pointLight1.color.setHex(isDark ? 0x1e88e5 : 0x42a5f5);
            pointLight2.color.setHex(isDark ? 0x42a5f5 : 0x90caf9);
        }
    }
}

// Function to render a word with Tajweed highlighting
function renderWord(word, wordIndex) {
    const tajweedClasses = word.tajweed ? word.tajweed.split(' ').map(t => t.trim()).join(' ') : '';
    return `<span class="word ${tajweedClasses}" data-word="${wordIndex}" data-root="${word.root}" data-trans="${word.trans}" data-translit="${word.translit}">${word.text}</span>`;
}

// Function to render an ayah
function renderAyah(ayah, ayahIndex) {
    const wordsHtml = ayah.words.map((word, wordIndex) => renderWord(word, wordIndex)).join(' ');
    const ayahNumber = ayahIndex + 1;
    const arabicNumber = ['١', '٢', '٣', '٤', '٥', '٦', '٧'][ayahIndex] || `${ayahNumber}`;
    
    return `
        <div class="ayah" data-ayah="${ayahIndex}">
            <div class="ayah-content">
                <p class="arabic" dir="rtl">
                    ${wordsHtml}
                    <span class="ayah-marker" data-number="${arabicNumber}"></span>
                </p>
                <p class="translation">${ayah.translation}</p>
                <p class="transliteration">${ayah.transliteration}</p>
                <div class="ayah-controls">
                    <button class="play-btn" aria-label="Play ayah">
                        <svg class="play-icon" viewBox="0 0 24 24" width="24" height="24">
                            <path class="play-path" d="M8 5v14l11-7z"/>
                        </svg>
                    </button>
                    <div class="options-menu">
                        <button class="options-btn" aria-label="More options">⋮</button>
                        <div class="options-content">
                            <div class="reciter-select">
                                <label>Select Reciter:</label>
                                <select>
                                    <option value="ayyoub">Sheikh Mohammad Ayyoub</option>
                                    <option value="hudhaify">Sheikh Ali Al-Hudhaify</option>
                                    <option value="maher">Sheikh Maher Al-Muaiqly</option>
                                    <option value="minshawy">Sheikh Mohamed Siddiq El-Minshawi</option>
                                    <option value="mishary">Sheikh Mishary Rashid Alafasy</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <audio class="ayah-audio"></audio>
                </div>
            </div>
        </div>
    `;
}

// Function to render a complete surah
function renderSurah(surahNumber) {
    const surah = surahData[surahNumber];
    if (!surah) return '';
    
    return surah.ayahs.map((ayah, index) => renderAyah(ayah, index)).join('');
}

// Function to transition between surahs with animation
function transitionToSurah(newSurahNumber) {
    if (currentSurah === newSurahNumber) return;
    
    const surahContainer = document.querySelector('.surah-container');
    const feedbackCards = document.querySelectorAll('.feedback-card');
    
    // Clear feedback cards
    feedbackCards.forEach(card => {
        const emptyState = card.querySelector('.empty-state');
        const feedbackMessages = card.querySelector('.feedback-messages');
        if (emptyState) emptyState.style.display = 'block';
        if (feedbackMessages) feedbackMessages.innerHTML = '<p class="empty-state">Feedback will appear here after recording</p>';
    });
    
    // Animate out current ayahs
    anime({
        targets: '.ayah',
        opacity: 0,
        translateX: -50,
        duration: 400,
        delay: anime.stagger(50),
        easing: 'easeInQuart',
        complete: function() {
            // Update current surah
            currentSurah = newSurahNumber;
            
            // Render new surah
            surahContainer.innerHTML = renderSurah(newSurahNumber);
            
            // Re-attach event listeners to new ayahs
            attachAyahEventListeners();
            
            // Animate in new ayahs
            anime({
                targets: '.ayah',
                opacity: [0, 1],
                translateX: [50, 0],
                duration: 600,
                delay: anime.stagger(100, {start: 200}),
                easing: 'easeOutQuart'
            });
            
            // Show success message
            const surah = surahData[newSurahNumber];
            showToast(`${surah.name} (${surah.arabicName})`);
        }
    });
}

// Function to attach event listeners to ayahs
function attachAyahEventListeners() {
    const ayahs = document.querySelectorAll('.ayah');
    ayahs.forEach(ayah => {
        // Remove any existing listeners to prevent duplicates
        ayah.removeEventListener('click', handleAyahClick);
        ayah.addEventListener('click', handleAyahClick);
    });
    
    // Re-attach word tooltip listeners
    attachWordTooltipListeners();
    
    // Re-attach audio control listeners
    attachAudioControlListeners();
}

// Function to attach word tooltip listeners
function attachWordTooltipListeners() {
    const words = document.querySelectorAll('.word');
    words.forEach(word => {
        word.removeEventListener('mouseenter', handleWordHover);
        word.removeEventListener('mouseleave', handleWordLeave);
        word.addEventListener('mouseenter', handleWordHover);
        word.addEventListener('mouseleave', handleWordLeave);
    });
}

// Function to attach audio control listeners
function attachAudioControlListeners() {
    const playBtns = document.querySelectorAll('.play-btn');
    const optionsBtns = document.querySelectorAll('.options-btn');
    
    playBtns.forEach(btn => {
        btn.removeEventListener('click', handlePlayClick);
        btn.addEventListener('click', handlePlayClick);
    });
    
    optionsBtns.forEach(btn => {
        btn.removeEventListener('click', handleOptionsClick);
        btn.addEventListener('click', handleOptionsClick);
    });
}

// Event handlers for word tooltips
function handleWordHover(e) {
    e.stopPropagation();
    const word = e.target;
    if (!word.classList.contains('word')) return;
    
    const tooltip = document.getElementById('root-tooltip');
    const root = word.getAttribute('data-root');
    const trans = word.getAttribute('data-trans');
    const translit = word.getAttribute('data-translit');
    
    if (root && trans && translit) {
        tooltip.innerHTML = `
            <div class="tooltip-content">
                <div class="root">Root: ${root}</div>
                <div class="trans">Meaning: ${trans}</div>
                <div class="translit">Pronunciation: ${translit}</div>
            </div>
        `;
        
        const rect = word.getBoundingClientRect();
        tooltip.style.left = `${rect.left + rect.width / 2}px`;
        tooltip.style.top = `${rect.bottom + 10}px`;
        tooltip.classList.add('show');
        word.classList.add('word-highlight');
    }
}

function handleWordLeave(e) {
    const tooltip = document.getElementById('root-tooltip');
    const word = e.target;
    tooltip.classList.remove('show');
    word.classList.remove('word-highlight');
}

// Event handlers for audio controls
function handlePlayClick(e) {
    e.stopPropagation();
    // Placeholder for audio functionality
    console.log('Play button clicked');
}

function handleOptionsClick(e) {
    e.stopPropagation();
    const optionsMenu = e.target.closest('.options-menu');
    optionsMenu.classList.toggle('active');
}

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing recording functionality');
    
    // Add click listeners to all ayahs
    const ayahs = document.querySelectorAll('.ayah');
    console.log('Found ayahs:', ayahs.length);

    ayahs.forEach(ayah => {
        console.log('Adding click listener to ayah:', ayah);
        ayah.addEventListener('click', handleAyahClick);
    });

    // Root word tooltip functionality
    const tooltip = document.getElementById('root-tooltip');
    let activeWord = null;

    function hideTooltip() {
        if (tooltipTimeout) {
            clearTimeout(tooltipTimeout);
        }
        tooltip.classList.add('fade-out');
        setTimeout(() => {
            tooltip.classList.remove('show', 'fade-out');
            if (activeWord) {
                activeWord.classList.remove('word-highlight');
                activeWord = null;
            }
        }, 300); // Wait for fade animation to complete
    }

    document.querySelectorAll('.word').forEach(word => {
        word.addEventListener('click', (e) => {
            const root = e.currentTarget.getAttribute('data-root');
            const trans = e.currentTarget.getAttribute('data-trans');
            const translit = e.currentTarget.getAttribute('data-translit');
            
            if (root) {
                // Clear any existing timeout
                if (tooltipTimeout) {
                    clearTimeout(tooltipTimeout);
                }
                
                // Get word's position
                const rect = e.currentTarget.getBoundingClientRect();
                
                // Position tooltip above the word
                tooltip.style.left = `${rect.left + (rect.width / 2)}px`;
                tooltip.style.top = `${rect.top - 40}px`;
                tooltip.style.transform = 'translate(-50%, -100%)';
                
                // Show root word, translation and transliteration
                tooltip.innerHTML = `
                    <div class="tooltip-content">
                        <div class="root">Root: ${root}</div>
                        <div class="trans">${trans}</div>
                        <div class="translit">${translit}</div>
                    </div>
                `;
                tooltip.classList.remove('fade-out');
                tooltip.classList.add('show');
                
                // Highlight clicked word
                if (activeWord) {
                    activeWord.classList.remove('word-highlight');
                }
                e.currentTarget.classList.add('word-highlight');
                activeWord = e.currentTarget;

                // Set timeout to hide tooltip after 2 seconds
                tooltipTimeout = setTimeout(hideTooltip, 2000);
            }
        });
    });

    // Hide tooltip when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.word')) {
            hideTooltip();
        }
    });

    // Theme Toggle
    const themeToggle = document.getElementById('themeToggle');
    const mobileThemeToggle = document.getElementById('mobileThemeToggle');
    const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Set initial theme based on localStorage or system preference
    const savedTheme = localStorage.getItem('theme');
    const isDark = savedTheme === 'dark' || (!savedTheme && prefersDarkScheme.matches);
    handleThemeChange(isDark);

    // Theme toggle click handlers
    const toggleTheme = () => {
        const isDark = document.body.getAttribute('data-theme') === 'dark';
        handleThemeChange(!isDark);
    };

    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    if (mobileThemeToggle) {
        mobileThemeToggle.addEventListener('click', toggleTheme);
    }

    // Listen for system theme changes
    prefersDarkScheme.addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) {
            handleThemeChange(e.matches);
        }
    });

    // Initialize ayah controls
    document.querySelectorAll('.ayah').forEach(ayah => {
        const playBtn = ayah.querySelector('.play-btn');
        const optionsBtn = ayah.querySelector('.options-btn');
        const optionsMenu = ayah.querySelector('.options-menu');
        const optionsContent = ayah.querySelector('.options-content');
        const audio = ayah.querySelector('.ayah-audio');
        const reciterSelect = ayah.querySelector('.reciter-select select');
        const ayahNumber = ayah.dataset.ayah;
        
        // Set initial reciter value
        reciterSelect.value = currentReciter;
        
        // Add mouseleave event to close options menu
        ayah.addEventListener('mouseleave', () => {
            optionsMenu.classList.remove('active');
        });
        
        // Play button functionality
        playBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent ayah click handler
            
            const isPlaying = playBtn.classList.contains('playing');
            
            // Stop all other playing audio
            document.querySelectorAll('.ayah-audio').forEach(otherAudio => {
                if (otherAudio !== audio) {
                    otherAudio.pause();
                    otherAudio.currentTime = 0;
                }
            });
            document.querySelectorAll('.play-btn').forEach(btn => {
                if (btn !== playBtn) {
                    btn.classList.remove('playing');
                }
            });
            
            if (isPlaying) {
                audio.pause();
                playBtn.classList.remove('playing');
            } else {
                audio.src = `/reference-audio/${currentReciter}/${parseInt(ayahNumber) + 1}`;
                audio.play()
                    .then(() => {
                        playBtn.classList.add('playing');
                    })
                    .catch(error => {
                        console.error('Error playing audio:', error);
                        alert('Error playing audio. Please try again.');
                    });
            }
        });
        
        // Options menu functionality
        optionsBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent ayah click handler
            
            // Close all other open menus
            document.querySelectorAll('.options-menu').forEach(menu => {
                if (menu !== optionsMenu) {
                    menu.classList.remove('active');
                }
            });
            
            optionsMenu.classList.toggle('active');
        });

        // Prevent clicks inside options content from closing the menu
        optionsContent.addEventListener('click', (e) => {
            e.stopPropagation();
        });

        // Handle reciter select clicks and changes
        reciterSelect.addEventListener('click', (e) => {
            e.stopPropagation();
        });
        
        // Handle reciter change
        reciterSelect.addEventListener('change', (e) => {
            e.stopPropagation();
            
            // Update global reciter
            currentReciter = e.target.value;
            
            // Update all other reciter selects
            document.querySelectorAll('.reciter-select select').forEach(select => {
                select.value = currentReciter;
            });
            
            // If this ayah is currently playing, update its source
            if (!audio.paused) {
                const currentTime = audio.currentTime;
                audio.src = `/reference-audio/${currentReciter}/${parseInt(ayahNumber) + 1}`;
                audio.currentTime = currentTime;
                audio.play()
                    .catch(error => {
                        console.error('Error playing audio:', error);
                        alert('Error playing audio. Please try again.');
                    });
            }
        });
        
        // Handle audio end
        audio.addEventListener('ended', () => {
            playBtn.classList.remove('playing');
        });
    });
    
    // Close options menu when clicking outside, but not when clicking inside options
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.options-content') && !e.target.closest('.options-btn')) {
            document.querySelectorAll('.options-menu').forEach(menu => {
                menu.classList.remove('active');
            });
        }
    });

    // Initialize surah selector
    const surahSelect = document.getElementById('surah-select');
    if (surahSelect) {
        surahSelect.addEventListener('change', function(e) {
            const selectedSurah = parseInt(e.target.value);
            const selectedOption = e.target.options[e.target.selectedIndex];
            
            // Handle surah selection
            if (selectedSurah === currentSurah) {
                const surah = surahData[selectedSurah];
                showToast(`Already on ${surah.name}`);
            } else if (selectedSurah === 1 || selectedSurah === 113) {
                // Transition to available surahs
                transitionToSurah(selectedSurah);
            } else {
                // Show coming soon message for other surahs
                showToast(`Coming soon! Only Al-Fatiha & Al-Falaq available.`);
                // Reset to current surah
                setTimeout(() => {
                    e.target.value = currentSurah.toString();
                }, 2000);
            }
        });
    }
});

// Handle ayah click
async function handleAyahClick(e) {
    console.log('handleAyahClick called');
    
    // Only prevent recording for specific interactive elements
    if (e.target.classList.contains('word') || 
        e.target.closest('.word') ||
        e.target.closest('.play-btn') ||
        e.target.closest('.options-btn') ||
        e.target.closest('.options-content')) {
        console.log('Clicked on word or control button, not starting recording');
        return;
    }
    
    e.preventDefault();
    e.stopPropagation();
    
    const ayah = e.currentTarget;
    console.log('Ayah clicked:', ayah.dataset.ayah, 'Current recording state:', isRecording);
    
    try {
        if (isRecording && currentRecordingAyah === ayah) {
            console.log('Stopping recording for current ayah');
            await stopRecording();
        } else {
            console.log('Starting recording');
            if (isRecording) {
                console.log('Stopping previous recording first');
                await stopRecording();
            }
            await startRecording(ayah);
        }
    } catch (err) {
        console.error('Error handling ayah click:', err);
        alert('Error with recording. Please ensure microphone permissions are granted.');
        await stopRecording();
    }
}

// Initialize WebSocket connection
function initializeWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws`);
    
    ws.onopen = () => {
        console.log('WebSocket connection established');
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        console.log('WebSocket connection closed');
    };
    
    ws.onmessage = function(event) {
        const response = JSON.parse(event.data);
        console.log('WebSocket message received:', response);
        if (response.type === 'transcription') {
            handleTranscription(response.text, response.ayah_number, response.word_index, response.has_error);
        } else if (response.type === 'error') {
            console.error('Server error:', response.message);
            alert('Error: ' + response.message);
        }
    };
}

// Handle transcription results
function handleTranscription(text, ayahNumber, wordIndex, hasError) {
    console.log('Handling transcription:', { text, ayahNumber, wordIndex, hasError });
    
    if (ayahNumber !== null && wordIndex !== null) {
        // Remove previous highlights
        document.querySelectorAll('.word.active').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.ayah.active').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.word.error').forEach(el => el.classList.remove('error'));
        
        // Highlight current ayah and word
        const ayah = document.querySelector(`.ayah[data-ayah="${ayahNumber}"]`);
        if (ayah) {
            ayah.classList.add('active');
            const words = ayah.querySelectorAll('.word');
            if (words[wordIndex]) {
                words[wordIndex].classList.add('active');
                if (hasError) {
                    words[wordIndex].classList.add('error');
                }
            }
        }
    }
}

// Start recording function
async function startRecording(ayah) {
    try {
        console.log('Starting recording for ayah:', ayah.dataset.ayah);
        
        // Initialize WebSocket first
        initializeWebSocket();
        
        // Wait for WebSocket connection to be established
        while (ws.readyState !== WebSocket.OPEN) {
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        // Send target ayah number
        ws.send(JSON.stringify({
            target_ayah: ayah.dataset.ayah
        }));
        
        // Request microphone permission with specific constraints
        console.log('Requesting microphone access...');
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                sampleRate: 16000,
                echoCancellation: true,
                noiseSuppression: true
            }
        });
        console.log('Microphone access granted, creating MediaRecorder...');
        
        // Create MediaRecorder instance with specific MIME type
        const options = {
            mimeType: 'audio/webm;codecs=opus',
            audioBitsPerSecond: 16000
        };
        
        try {
            mediaRecorder = new MediaRecorder(stream, options);
            console.log('MediaRecorder created successfully');
        } catch (e) {
            console.warn('Failed to create MediaRecorder with preferred options, trying fallback...', e);
            // Fallback to default options
            mediaRecorder = new MediaRecorder(stream);
        }
        
        audioChunks = [];
        
        // Add recording class immediately for visual feedback
        ayah.classList.add('recording');
        currentRecordingAyah = ayah;
        
        // Handle data available event
        mediaRecorder.ondataavailable = async (event) => {
            console.log('Data available from MediaRecorder, size:', event.data.size);
            if (event.data.size > 0) {
                audioChunks.push(event.data);
                
                // Convert WebM chunk to WAV before sending
                const audioContext = new AudioContext();
                const arrayBuffer = await event.data.arrayBuffer();
                const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
                
                // Create WAV file
                const wavData = audioBufferToWav(audioBuffer);
                const wavBlob = new Blob([wavData], { type: 'audio/wav' });
                
                // Send WAV data through WebSocket
                if (ws && ws.readyState === WebSocket.OPEN) {
                    const buffer = await wavBlob.arrayBuffer();
                    console.log('Sending WAV audio chunk, size:', buffer.byteLength);
                    ws.send(buffer);
                } else {
                    console.warn('WebSocket not ready, chunk not sent');
                }
            }
        };

        // Function to convert AudioBuffer to WAV format
        function audioBufferToWav(buffer) {
            const numOfChan = buffer.numberOfChannels;
            const length = buffer.length * numOfChan * 2;
            const sampleRate = buffer.sampleRate;
            const data = new DataView(new ArrayBuffer(44 + length));
            
            // WAV Header
            writeString(data, 0, 'RIFF');
            data.setUint32(4, 36 + length, true);
            writeString(data, 8, 'WAVE');
            writeString(data, 12, 'fmt ');
            data.setUint32(16, 16, true);
            data.setUint16(20, 1, true);
            data.setUint16(22, numOfChan, true);
            data.setUint32(24, sampleRate, true);
            data.setUint32(28, sampleRate * numOfChan * 2, true);
            data.setUint16(32, numOfChan * 2, true);
            data.setUint16(34, 16, true);
            writeString(data, 36, 'data');
            data.setUint32(40, length, true);
            
            // Write audio data
            const offset = 44;
            const channelData = [];
            for (let i = 0; i < numOfChan; i++) {
                channelData.push(buffer.getChannelData(i));
            }
            
            let pos = 0;
            while (pos < buffer.length) {
                for (let i = 0; i < numOfChan; i++) {
                    const sample = Math.max(-1, Math.min(1, channelData[i][pos]));
                    data.setInt16(offset + (pos * numOfChan + i) * 2, sample < 0 ? sample * 0x8000 : sample * 0x7FFF, true);
                }
                pos++;
            }
            
            return data.buffer;
        }

        // Helper function to write strings to DataView
        function writeString(view, offset, string) {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        }

        // Handle recording stop
        mediaRecorder.onstop = async () => {
            console.log('MediaRecorder stopped');
            if (ws && ws.readyState === WebSocket.OPEN) {
                // Send done message to server
                ws.send(JSON.stringify({ type: 'done' }));
            }
            if (ws) {
                ws.close();
            }
            // Convert the recorded audioChunks (WebM/Opus) to WAV
            const webmBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const arrayBuffer = await webmBlob.arrayBuffer();
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            let audioBuffer;
            try {
                audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            } catch (err) {
                console.error('Unable to decode audio data:', err);
                showToast('Error decoding audio. Please try again.');
                return;
            }
            // Now convert AudioBuffer to WAV
            const wavData = audioBufferToWav(audioBuffer);
            const wavBlob = new Blob([wavData], { type: 'audio/wav' });
            // Send the real WAV blob to the backend
            await sendAudioToServer(wavBlob);
        };

        // Handle recording errors
        mediaRecorder.onerror = (event) => {
            console.error('MediaRecorder error:', event.error);
            alert('Error during recording: ' + event.error.message);
            stopRecording().catch(console.error);
        };

        // Start recording with smaller time slices for more frequent updates
        mediaRecorder.start(100);
        isRecording = true;
        console.log('Recording started successfully');
        
    } catch (err) {
        console.error('Error starting recording:', err);
        alert('Error accessing microphone. Please ensure microphone permissions are granted and try again.');
        // Clean up UI if there's an error
        if (currentRecordingAyah) {
            currentRecordingAyah.classList.remove('recording');
        }
        currentRecordingAyah = null;
        isRecording = false;
        throw err; // Re-throw to be handled by caller
    }
}

// Stop recording function
async function stopRecording() {
    console.log('Stopping recording');
    
    try {
        if (isRecording && mediaRecorder) {
            // Stop MediaRecorder
            if (mediaRecorder.state !== 'inactive') {
                console.log('Stopping MediaRecorder');
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(track => {
                    track.stop();
                    console.log('Stopped audio track:', track.label);
                });
            }
            
            // Show processing message
            const randomMessage = processingMessages[Math.floor(Math.random() * processingMessages.length)];
            document.querySelector('.feedback-card:first-child').innerHTML = `
                <h3>Recorded Recitation</h3>
                <p class="processing-message">${randomMessage}<span class="dots"></span></p>
            `;
            document.querySelector('.feedback-card:last-child').innerHTML = `
                <h3>Tajweed Feedback</h3>
                <p class="processing-message">Analyzing your recitation<span class="dots"></span></p>
            `;
            
            // Close WebSocket connection
            if (ws) {
                console.log('Closing WebSocket connection');
                ws.close();
                ws = null;
            }
            
            // Remove recording UI feedback
            if (currentRecordingAyah) {
                console.log('Removing recording UI from ayah:', currentRecordingAyah.dataset.ayah);
                currentRecordingAyah.classList.remove('recording');
                currentRecordingAyah = null;
            }
            
            isRecording = false;
            mediaRecorder = null;
            console.log('Recording stopped successfully');
        }
    } catch (err) {
        console.error('Error stopping recording:', err);
        // Clean up state even if there's an error
        isRecording = false;
        mediaRecorder = null;
        ws = null;
        if (currentRecordingAyah) {
            currentRecordingAyah.classList.remove('recording');
            currentRecordingAyah = null;
        }
        throw err; // Re-throw to be handled by caller
    }
}

// Function to highlight active ayah and word
function highlightAyah(ayahNumber, word = null) {
    // Remove previous highlights
    document.querySelectorAll('.ayah.active').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.word.active').forEach(el => el.classList.remove('active'));
    
    // Highlight new ayah
    const ayah = document.querySelector(`.ayah[data-ayah="${ayahNumber}"]`);
    if (ayah) {
        ayah.classList.add('active');
        
        // Scroll to ayah smoothly
        ayah.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Highlight specific word if provided
        if (word) {
            const wordEl = ayah.querySelector(`.word[data-word="${word}"]`);
            if (wordEl) {
                wordEl.classList.add('active');
            }
        }
    }
}

// Send audio to server for analysis
async function sendAudioToServer(audioBlob) {
    console.log('Sending audio to server');
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');

    // Show loading state for Madd feedback
    showMaddLoadingCard();

    try {
        // 1. Send to /analyze (existing Tajweed feedback)
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });
        const result = await response.json();
        console.log('Server response:', result);
        let tajweedFeedbackHtml = '';
        if (result.success) {
            tajweedFeedbackHtml = result.feedback.map(message => {
                let messageClass = 'feedback-message ';
                let icon = '';
                if (message.startsWith('✅')) {
                    messageClass += 'feedback-success';
                    icon = '✅';
                } else if (message.startsWith('⚠️')) {
                    messageClass += 'feedback-warning';
                    icon = '⚠️';
                } else if (message.startsWith('ℹ️')) {
                    messageClass += 'feedback-info';
                    icon = 'ℹ️';
                } else {
                    messageClass += 'feedback-error';
                    icon = '❌';
                }
                return `
                    <div class="${messageClass}">
                        <span class="feedback-icon">${icon}</span>
                        <span>${message.replace(/[✅⚠️ℹ️❌]/g, '').trim()}</span>
                    </div>
                `;
            }).join('');
        } else {
            tajweedFeedbackHtml = `
                <div class="feedback-message feedback-error">
                    <span class="feedback-icon">❌</span>
                    <span>Error: ${result.error}</span>
                </div>
            `;
        }

        // 2. Send to /madd-audio-analysis (Madd feedback)
        const maddFormData = new FormData();
        maddFormData.append('audio', audioBlob, 'recording.wav');
        showMaddLoadingCard();
        let maddResults = null;
        let maddDebug = null;
        let maddStatus = 'analyzing';
        try {
            const maddResponse = await fetch('/madd-audio-analysis', {
                method: 'POST',
                body: maddFormData
            });
            const maddJson = await maddResponse.json();
            maddResults = maddJson.results || [];
            maddDebug = maddJson.debug || [];
            maddStatus = maddJson.status;
        } catch (err) {
            maddResults = [];
            maddDebug = [String(err)];
            maddStatus = 'error';
        }
        renderMaddFeedbackCard(maddResults, maddDebug, maddStatus);

        // 3. Render all feedback cards
        document.getElementById('feedback').innerHTML = `
            <div class="feedback-section">
                <div class="feedback-card">
                    <h3>Recorded Recitation</h3>
                    <p dir="rtl" class="arabic">${result.transcription || ''}</p>
                </div>
                <div class="feedback-card">
                    <h3>Tajweed Feedback</h3>
                    <div class="feedback-messages">
                        ${tajweedFeedbackHtml}
                    </div>
                </div>
                <div id="madd-feedback-card"></div>
                <div id="madd-debug-box"></div>
            </div>
        `;
        renderMaddFeedbackCard(maddResults, maddDebug, maddStatus);
    } catch (error) {
        console.error('Error sending audio:', error);
        document.getElementById('feedback').innerHTML = `
            <div class="feedback-section">
                <div class="feedback-card">
                    <div class="feedback-message feedback-error">
                        <span class="feedback-icon">❌</span>
                        <span>Error sending recording to server</span>
                    </div>
                </div>
            </div>
        `;
    }
}

function showMaddLoadingCard() {
    const maddCard = document.getElementById('madd-feedback-card');
    if (maddCard) {
        maddCard.innerHTML = `
            <div class="feedback-card madd-card">
                <h3>Madd (Prolongation) Feedback</h3>
                <p class="processing-message">Analyzing Madd... <span class="dots"></span></p>
            </div>
        `;
    }
    const debugBox = document.getElementById('madd-debug-box');
    if (debugBox) {
        debugBox.innerHTML = '';
    }
}

function renderMaddFeedbackCard(maddResults, maddDebug, maddStatus) {
    const maddCard = document.getElementById('madd-feedback-card');
    const debugBox = document.getElementById('madd-debug-box');
    if (!maddCard) return;
    if (maddStatus === 'analyzing') {
        showMaddLoadingCard();
        return;
    }
    if (maddStatus === 'error') {
        maddCard.innerHTML = `
            <div class="feedback-card madd-card">
                <h3>Madd (Prolongation) Feedback</h3>
                <div class="feedback-message feedback-error">
                    <span class="feedback-icon">❌</span>
                    <span>Error analyzing Madd</span>
                </div>
            </div>
        `;
        debugBox.innerHTML = '';
        return;
    }
    if (!maddResults || maddResults.length === 0) {
        maddCard.innerHTML = `
            <div class="feedback-card madd-card">
                <h3>Madd (Prolongation) Feedback</h3>
                <div class="feedback-message feedback-info">
                    <span class="feedback-icon">ℹ️</span>
                    <span>No Madd detected in this ayah.</span>
                </div>
            </div>
        `;
    } else {
        maddCard.innerHTML = `
            <div class="feedback-card madd-card">
                <h3>Madd (Prolongation) Feedback</h3>
                <div class="madd-results">
                    ${maddResults.map(madd => `
                        <div class="madd-row">
                            <span class="madd-icon">${madd.madd_detected ? '✅' : '❌'}</span>
                            <span class="madd-word">${madd.word}</span>
                            <span class="madd-letter">(${madd.letter})</span>
                            <span class="madd-type">${madd.type}</span>
                            <span class="madd-expected">${madd.text_expected ? '<span class="madd-expected-yes">Expected</span>' : '<span class="madd-expected-no">Not Expected</span>'}</span>
                            <span class="madd-feedback-msg">${madd.feedback}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    // Debug box (collapsible)
    debugBox.innerHTML = `
        <div class="madd-debug-container">
            <button class="madd-debug-toggle" aria-expanded="false" onclick="toggleDebugJson(this)">Show Madd Debug JSON</button>
            <pre class="madd-debug-json">${JSON.stringify(maddDebug, null, 2)}</pre>
        </div>
    `;
}

function toggleDebugJson(button) {
    const isExpanded = button.getAttribute('aria-expanded') === 'true';
    button.setAttribute('aria-expanded', !isExpanded);
    button.textContent = isExpanded ? 'Show Madd Debug JSON' : 'Hide Madd Debug JSON';
    const jsonElement = button.nextElementSibling;
    jsonElement.classList.toggle('show');
}

// Show toast message function
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.remove();
    }, 3000);
} 