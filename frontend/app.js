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

