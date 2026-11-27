
// Get the HTML elements
const loginForm = document.getElementById("login-form");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const togglePassword = document.getElementById("toggle-password");
const message = document.getElementById("message");
const submitButton = loginForm.querySelector('button[type="submit"]');

// Show or hide password
togglePassword.addEventListener("click", function () {
    const isHidden = passwordInput.type === "password";

    passwordInput.type = isHidden ? "text" : "password";
    togglePassword.textContent = isHidden ? "Hide" : "Show";

    togglePassword.setAttribute(
        "aria-label",
        isHidden ? "Hide password" : "Show password"
    );
});

// Handle login form submission
loginForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    if (submitButton.disabled) return;

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    submitButton.disabled = true;
    message.classList.remove("error");
    message.textContent = "Checking your credentials…";

    try {
        const response = await fetch(loginForm.action, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        });
        const data = await response.json().catch(() => ({}));
        if (response.ok && data.message === "Logged in.") {
            passwordInput.value = "";
            window.location.assign("index.html");
        } else {
            message.classList.add("error");
            message.textContent = data.error || "Could not sign in. Try again.";
        }
    } catch {
        message.classList.add("error");
        message.textContent = "Could not reach the server. Try again.";
    } finally {
        submitButton.disabled = false;
    }
});
