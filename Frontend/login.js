
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
loginForm.addEventListener("submit", function (event) {
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

    // Frontend-only demonstration
    message.textContent =
        "Form validated. Backend login is not connected yet.";

    console.log("Login form validated.");
});
