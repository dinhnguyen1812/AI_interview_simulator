let sessionId = null;

async function startSession() {
  const topic = document.getElementById('topic').value;
  const difficulty = document.getElementById('difficulty').value;

  const res = await fetch("http://localhost:8000/interview/question", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ topic, difficulty }),
  });

  const data = await res.json();
  sessionId = data.session_id;

  document.getElementById('session').innerHTML = `
    <p><strong>Question:</strong> ${data.question}</p>
    <textarea id="answer" rows="4" cols="60" placeholder="Your answer here..."></textarea><br />
    <button onclick="submitAnswer()">Submit Answer</button>
  `;
}

async function submitAnswer() {
  const answer = document.getElementById('answer').value;

  const res = await fetch("http://localhost:8000/interview/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, answer }),
  });

  const data = await res.json();
  document.getElementById('session').innerHTML += `
    <p><strong>Feedback:</strong> ${data.feedback}</p>
    <p><strong>Score:</strong> ${data.score}</p>
  `;
}

// Handle register form
const registerForm = document.getElementById("register-form");
if (registerForm) {
  registerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const res = await fetch("http://localhost:8000/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    document.getElementById("register-msg").innerText = res.ok
      ? "Registered successfully!"
      : "Registration failed.";
  });
}

// Handle login form
const loginForm = document.getElementById("login-form");
if (loginForm) {
  loginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const res = await fetch("http://localhost:8000/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include", // <-- Important for cookie
      body: JSON.stringify({ email, password }),
    });
    document.getElementById("login-msg").innerText = res.ok
      ? "Logged in successfully!"
      : "Login failed.";
  });
}