let sessionId = null;

async function startSession() {
  const role = document.getElementById("role").value;
  const experience = document.getElementById("experience").value;
  const tech_stack = document.getElementById("tech_stack").value;
  const difficulty = document.getElementById("difficulty").value;

  const res = await fetch("http://localhost:8000/interview/question", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      role,
      experience,
      tech_stack,
      difficulty
    })
  });

  const data = await res.json();
  sessionId = data.session_id;

  document.getElementById("session").innerHTML = `
    <p><strong>Question:</strong> ${data.question}</p>
    <textarea id="answer" rows="4" cols="60" placeholder="Your answer here..."></textarea><br />
    <button onclick="submitAnswer()">Submit Answer</button>
  `;

  // Reload session history immediately after new session starts
  loadSessionHistory();
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
    if (res.ok) {
      // ✅ Redirect after successful registration
      window.location.href = "/static/login.html";
    } else {
      document.getElementById("register-msg").innerText = "Registration failed.";
    }
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
      credentials: "include",
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();

    if (res.ok) {
      // ✅ Store values in localStorage
      localStorage.setItem("user_role", data.role || "");
      localStorage.setItem("user_experience", data.experience || "");
      localStorage.setItem("user_tech_stack", data.tech_stack || "");

      // ✅ Redirect to homepage
      window.location.href = "/static/index.html";
    } else {
      document.getElementById("login-msg").innerText = "Login failed.";
    }
  });
}


// Show logged-in user email at top right if logged in
async function showUserEmail() {
  const path = window.location.pathname;

  // Skip on login or register pages
  if (path.includes("login.html") || path.includes("register.html")) return;

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

    // Add logout button
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
        // Redirect after logout
        window.location.href = "/static/login.html";
      };
      userElem.appendChild(logoutBtn);
    }
  } catch {
    // If on index page and not logged in, redirect to login
    if (path.endsWith("index.html") || path === "/") {
      window.location.href = "/static/login.html";
    }
  }
}

// Always call on page load
showUserEmail();

// Show session history of an user
async function loadSessionHistory() {
  try {
    const res = await fetch("/user/session", {
      credentials: "include",
    });
    if (!res.ok) throw new Error("Failed to fetch user session history");

    const data = await res.json();

    let container = document.getElementById("session-history");
    if (!container) {
      container = document.createElement("div");
      container.id = "session-history";
      container.style.marginTop = "20px";
      document.body.appendChild(container);
    }

    if (data.sessions.length === 0) {
      container.textContent = "No previous sessions found.";
      return;
    }

    container.innerHTML = "<h3>Your Previous Sessions</h3>";
    const list = document.createElement("ul");
    data.sessions.forEach(session => {
      const li = document.createElement("li");
      const timestamp = session.created_at
        ? new Date(session.created_at).toLocaleString()
        : "unknown time";

      const link = document.createElement("a");
      link.href = "#";
      link.textContent = `Session on ${timestamp}`;
      link.onclick = () => loadSessionDetail(session.id);

      li.appendChild(link);
      list.appendChild(li);
    });
    container.appendChild(list);

  } catch (error) {
    console.error(error);
  }
}

// Call this after confirming user is logged in on index page
if (window.location.pathname.endsWith("index.html") || window.location.pathname === "/") {
  showUserEmail().then(() => {
    loadSessionHistory();
  });
}

async function loadSessionDetail(sessionId) {
  try {
    const res = await fetch(`/session/${sessionId}`, {
      credentials: "include",
    });
    if (!res.ok) throw new Error("Failed to fetch session detail");

    const data = await res.json();

    const container = document.getElementById("session");
    container.innerHTML = `<h3>Session Detail</h3>`;

    if (!data.interactions || data.interactions.length === 0) {
      container.innerHTML += `<p>No interactions found for this session.</p>`;
      return;
    }

    const list = document.createElement("ol");
    data.interactions.forEach(log => {
      const li = document.createElement("li");
      li.innerHTML = `
        <strong>Q:</strong> ${log.question}<br />
        <strong>A:</strong> ${log.answer || "<em>No answer submitted</em>"}<br />
        <strong>Score:</strong> ${log.score ?? "N/A"}<br />
        <strong>Feedback:</strong> ${log.feedback ?? "No feedback"}<br />
        <em>${new Date(log.timestamp).toLocaleString()}</em>
      `;
      list.appendChild(li);
    });

    container.appendChild(list);

  } catch (err) {
    console.error("Error loading session detail:", err);
  }
}

async function getAdvice() {
  try {
    const res = await fetch("/interview/advice", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    });

    const data = await res.json();

    if (res.ok) {
      const adviceBox = document.getElementById("advice-box");
      adviceBox.innerHTML = formatAdvice(data.advice);
    } else {
      alert(data.detail || "Failed to get advice.");
    }
  } catch (error) {
    console.error("Error fetching advice:", error);
  }
}

// Format the plain text advice into structured HTML
function formatAdvice(text) {
  // Convert markdown-style bold **text** to HTML <strong>text</strong>
  let html = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

  // Optional: turn newlines into <br> if desired (only for better formatting)
  html = html.replace(/\n/g, "<br>");

  // Wrap in styled HTML
  return `
    <h3>Improvement Advice</h3>
    <div style="line-height: 1.6;">${html}</div>
  `;
}

