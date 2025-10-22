document.addEventListener('DOMContentLoaded', function() {
  const questions = document.querySelectorAll('.question');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const submitBtn = document.getElementById('submitBtn');
  const navContainer = document.getElementById('questionNav');
  const progress = document.getElementById('progress');
  let currentQuestion = 0;

  // ✅ Build numbered question buttons (updated: add utility classes so they show as boxes with CDN)
  const btnWrapper = document.createElement('div');
  btnWrapper.classList.add('nav-grid'); // CSS in your HTML should style this (.nav-grid -> grid layout)
  navContainer.appendChild(btnWrapper);

  questions.forEach((_, i) => {
    const btn = document.createElement('button');
    btn.textContent = i + 1;
    btn.type = 'button';

    // visible base styles (Tailwind utility classes are safe with CDN)
    btn.classList.add(
      'nav-btn',               // base class (we style .nav-btn in plain CSS in the template)
      'w-10', 'h-10',          // size
      'flex', 'items-center', 'justify-center',
      'rounded-md',
      'border', 'border-gray-300',
      'text-gray-700', 'bg-gray-200',
      'hover:bg-blue-400', 'hover:text-white',
      'transition', 'duration-200',
      'font-medium',
      'focus:outline-none'
    );

    btn.addEventListener('click', () => showQuestion(i));
    btnWrapper.appendChild(btn);
  });

  const navButtons = navContainer.querySelectorAll('.nav-btn');

  function showQuestion(index) {
    if (index < 0 || index >= questions.length) return;
    questions.forEach((q, i) => q.style.display = i === index ? 'block' : 'none');
    currentQuestion = index;
    updateNavButtons();
    updateButtons();

    // ensure the current nav button is visible in the nav panel (scroll into view)
    const activeBtn = navButtons[currentQuestion];
    if (activeBtn && typeof activeBtn.scrollIntoView === 'function') {
      // only scroll if the nav panel is scrollable; use nearest block to avoid jumping the whole page
      activeBtn.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    }
  }

  function updateNavButtons() {
    navButtons.forEach((btn, i) => {
      btn.classList.toggle('active', i === currentQuestion);
    });
  }

  function updateButtons() {
    progress.textContent = `Question ${currentQuestion + 1} of ${questions.length}`;
    prevBtn.style.display = currentQuestion === 0 ? 'none' : 'inline-block';
    nextBtn.style.display = currentQuestion === questions.length - 1 ? 'none' : 'inline-block';
    submitBtn.style.display = currentQuestion === questions.length - 1 ? 'inline-block' : 'none';
  }

  // ✅ Update answered states
  document.querySelectorAll('input[type="radio"]').forEach(input => {
    input.addEventListener('change', () => {
      const qDiv = input.closest('.question');
      const index = parseInt(qDiv.dataset.index);
      if (navButtons[index]) {
        navButtons[index].classList.add('answered');
      }
    });
  });

  // ✅ Navigation buttons
  nextBtn.addEventListener('click', () => {
    if (currentQuestion < questions.length - 1) showQuestion(currentQuestion + 1);
  });
  prevBtn.addEventListener('click', () => {
    if (currentQuestion > 0) showQuestion(currentQuestion - 1);
  });

  // ✅ Initialize first question
  showQuestion(0);
});

// ================== TIMER ==================
const timerDisplay = document.getElementById('timer');
let totalSeconds = 3600; // 60 minutes

function updateTimer() {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (timerDisplay) {
    timerDisplay.textContent = `Time Left: ${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

    // Turn red in last 5 minutes
    if (totalSeconds <= 300) {
      timerDisplay.style.color = 'red';
      timerDisplay.style.fontWeight = 'bold';
    }
  }

  if (totalSeconds <= 0) {
    clearInterval(timerInterval);
    alert('Time is up! Your exam will be submitted.');
    const form = document.getElementById('examForm');
    if (form) form.submit();
  }

  totalSeconds--;
}

const timerInterval = setInterval(updateTimer, 1000);
updateTimer();
