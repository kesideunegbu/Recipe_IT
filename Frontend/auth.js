
// Shared login check for pages that need a logged-in user.
// Sends the user to the login page if they are not logged in, and wires up
// the logout button if the page has one.

async function loadCurrentUser() {
    try {
        const response = await fetch("/api/me");
        if (response.status === 401) {
            window.location.href = "login.html";
            return null;
        }
        if (!response.ok) {
            return null;
        }
        return await response.json();
    } catch (error) {
        return null;
    }
}

async function logout() {
    try {
        await fetch("/api/logout", { method: "POST" });
    } finally {
        window.location.href = "login.html";
    }
}

loadCurrentUser().then(function (user) {
    const emailSlot = document.getElementById("user-email");
    if (user && emailSlot) {
        emailSlot.textContent = user.email;
    }
});

const logoutButton = document.getElementById("logout-btn");
if (logoutButton) {
    logoutButton.addEventListener("click", logout);
}
