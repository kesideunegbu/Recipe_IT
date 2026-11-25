
// Sign-up page: create the account, then log in and go to the main page.

const registerForm = document.getElementById("register-form");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const togglePassword = document.getElementById("toggle-password");
const message = document.getElementById("message");

togglePassword.addEventListener("click", function () {
    const isHidden = passwordInput.type === "password";
    passwordInput.type = isHidden ? "text" : "password";
    togglePassword.textContent = isHidden ? "Hide" : "Show";
    togglePassword.setAttribute(
        "aria-label",
        isHidden ? "Hide password" : "Show password"
    );
});

function showError(text) {
    message.textContent = text;
    message.className = "error";
}

async function postJson(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    const data = await response.json().catch(() => ({}));
    return { ok: response.ok, data };
}

registerForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const email = emailInput.value.trim();
    const password = passwordInput.value;
    message.textContent = "";
    message.className = "";

    if (!email || !password) {
        showError("Please fill in all fields.");
        return;
    }
    if (!emailInput.validity.valid) {
        showError("Please enter a valid email.");
        return;
    }
    if (password.length < 8) {
        showError("Password must be at least 8 characters.");
        return;
    }

    const submitButton = registerForm.querySelector("button[type=submit]");
    submitButton.disabled = true;

    try {
        const created = await postJson("/api/register", { email, password });
        if (!created.ok) {
            showError(created.data.error || "Sign up failed. Please try again.");
            return;
        }
        // Registering doesn't log in, so log in with the same details.
        const loggedIn = await postJson("/api/login", { email, password });
        window.location.href = loggedIn.ok ? "index.html" : "login.html";
    } catch (error) {
        showError("Could not reach the server. Please try again.");
    } finally {
        submitButton.disabled = false;
    }
});
