const form = document.getElementById("register-form");
const email = document.getElementById("email");
const password = document.getElementById("password");
const confirmation = document.getElementById("confirm-password");
const toggle = document.getElementById("toggle-password");
const submit = form.querySelector('button[type="submit"]');
const message = document.getElementById("message");

toggle.addEventListener("click", () => {
    const show = password.type === "password";
    password.type = confirmation.type = show ? "text" : "password";
    toggle.textContent = show ? "Hide" : "Show";
    toggle.setAttribute("aria-label", show ? "Hide passwords" : "Show passwords");
});

form.addEventListener("input", () => {
    confirmation.setCustomValidity("");
    message.textContent = "";
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (submit.disabled) return;

    if (password.value !== confirmation.value) {
        confirmation.setCustomValidity("Passwords do not match.");
        confirmation.reportValidity();
        return;
    }

    submit.disabled = true;
    message.classList.remove("error");
    message.textContent = "Creating your account…";

    try {
        const response = await fetch(form.action, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: email.value.trim(), password: password.value }),
        });
        if (response.status === 201) {
            form.reset();
            form.hidden = true;
            message.textContent = "Your account was created.";
            document.querySelector(".signup-text").textContent = "";
            const signIn = document.createElement("a");
            signIn.href = "login.html";
            signIn.textContent = "Back to sign in";
            document.querySelector(".signup-text").append(signIn);
            signIn.focus();
            return;
        }

        const data = await response.json().catch(() => ({}));
        message.classList.add("error");
        message.textContent = data.error || "Could not create your account. Try again.";
    } catch {
        message.classList.add("error");
        message.textContent = "Could not reach the server. Try again.";
    } finally {
        submit.disabled = false;
    }
});
