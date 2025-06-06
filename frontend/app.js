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

// Show logged-in user email at top right if logged in
async function showUserEmail() {
  try {
    const res = await fetch("/auth/user", {
      credentials: "include",
    });
    if (!res.ok) throw new Error("Not logged in");
    const data = await res.json();

    // Create or update user email display element
    let userElem = document.getElementById("user-email");
    if (!userElem) {
      userElem = document.createElement("div");
      userElem.id = "user-email";
      userElem.style.position = "fixed";
      userElem.style.top = "10px";
      userElem.style.right = "10px";
      userElem.style.backgroundColor = "#eee";
      userElem.style.padding = "5px 10px";
      userElem.style.borderRadius = "5px";
      document.body.appendChild(userElem);
    }
    userElem.textContent = `Logged in as: ${data.email}`;

    // Add logout button next to email
    let logoutBtn = document.getElementById("logout-btn");
    if (!logoutBtn) {
      logoutBtn = document.createElement("button");
      logoutBtn.id = "logout-btn";
      logoutBtn.textContent = "Logout";
      logoutBtn.style.marginLeft = "10px";
      logoutBtn.onclick = async () => {
        await fetch("/auth/logout", {
          method: "POST",
          credentials: "include",
        });
        // Redirect to login page after logout
        window.location.href = "/static/login.html";
      };
      userElem.appendChild(logoutBtn);
    }
  } catch {
    // No logged in user, do nothing
  }
}

// Call on page load
if (window.location.pathname.endsWith("index.html") || window.location.pathname === "/") {
  showUserEmail();
}
