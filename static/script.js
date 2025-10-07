document.addEventListener('DOMContentLoaded', function() {
  const questions = document.querySelectorAll('.question');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const submitBtn = document.getElementById('submitBtn');
  const navContainer = document.getElementById('questionNav');
  const progress = document.getElementById('progress');
  let currentQuestion = 0;

  // ✅ Build numbered question buttons
  questions.forEach((_, i) => {
    const btn = document.createElement('button');
    btn.textContent = i + 1;
    btn.classList.add('nav-btn');
    btn.type = 'button';
    btn.addEventListener('click', () => showQuestion(i));
    navContainer.appendChild(btn);
  });

  const navButtons = navContainer.querySelectorAll('.nav-btn');

  function showQuestion(index) {
    if (index < 0 || index >= questions.length) return;
    questions.forEach((q, i) => q.style.display = i === index ? 'block' : 'none');
    currentQuestion = index;
    updateNavButtons();
    updateButtons();
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
      navButtons[index].classList.add('answered');
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
  timerDisplay.textContent = `Time Left: ${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;

  // Turn red in last 5 minutes
  if (totalSeconds <= 300) {
    timerDisplay.style.color = 'red';
    timerDisplay.style.fontWeight = 'bold';
  }

  if (totalSeconds <= 0) {
    clearInterval(timerInterval);
    alert('Time is up! Your exam will be submitted.');
    document.getElementById('examForm').submit();
  }

  totalSeconds--;
}

const timerInterval = setInterval(updateTimer, 1000);
updateTimer();
