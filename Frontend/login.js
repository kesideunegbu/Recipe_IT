
// Get the HTML elements
const loginForm = document.getElementById("login-form");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const togglePassword = document.getElementById("toggle-password");
const message = document.getElementById("message");

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

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    message.className = "";

    // Check for empty fields
    if (!email || !password) {
        message.textContent = "Please fill in all fields.";
        message.className = "error";
        return;
    }

    // Check email format
    if (!emailInput.validity.valid) {
        message.textContent = "Please enter a valid email.";
        message.className = "error";
        return;
    }

    // Send the login to the backend. On success the server sets a session
    // cookie, so later requests know who the user is.
    const submitButton = loginForm.querySelector("button[type=submit]");
    submitButton.disabled = true;
    message.textContent = "";

    try {
        const response = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
        });

        if (response.ok) {
            window.location.href = "index.html";
            return;
        }

        const data = await response.json().catch(() => ({}));
        message.textContent = data.error || "Login failed. Please try again.";
        message.className = "error";
    } catch (error) {
        message.textContent =
            "Could not reach the server. Please try again.";
        message.className = "error";
    } finally {
        submitButton.disabled = false;
    }
});
