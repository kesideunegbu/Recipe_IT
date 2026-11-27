const pantryForm = document.getElementById("pantry-form");
const ingredientInput = document.getElementById("ingredient");
const ingredients = document.getElementById("ingredients");
const pantryEmpty = document.getElementById("pantry-empty");
const pantryStatus = document.getElementById("pantry-status");
const pantry = new Set();

pantryForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const added = [];

    for (const item of ingredientInput.value.split(",")) {
        const ingredient = item.trim().toLowerCase();
        if (!ingredient || pantry.has(ingredient)) continue;
        pantry.add(ingredient);
        added.push(ingredient);

        const entry = document.createElement("li");
        const remove = document.createElement("button");
        remove.type = "button";
        remove.textContent = ingredient + " ×";
        remove.setAttribute("aria-label", "Remove " + ingredient);
        remove.addEventListener("click", () => {
            pantry.delete(ingredient);
            entry.remove();
            pantryEmpty.hidden = pantry.size > 0;
            pantryStatus.textContent = "Removed " + ingredient + ".";
            ingredientInput.focus();
        });
        entry.append(remove);
        ingredients.append(entry);
    }

    pantryEmpty.hidden = pantry.size > 0;
    pantryStatus.textContent = added.length ? "Added " + added.join(", ") + "." : "No new ingredients added.";
    pantryForm.reset();
    ingredientInput.focus();
});

const chatForm = document.getElementById("chat-form");
const promptInput = document.getElementById("prompt");
const conversation = document.getElementById("conversation");

for (const suggestion of document.querySelectorAll(".suggestions button")) {
    suggestion.addEventListener("click", () => {
        promptInput.value = suggestion.textContent;
        promptInput.focus();
    });
}

chatForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const prompt = promptInput.value.trim();
    if (!prompt) return;

    const message = document.createElement("p");
    message.className = "user-message";
    message.textContent = prompt;
    conversation.append(message);
    conversation.scrollTop = conversation.scrollHeight;
    chatForm.reset();
    promptInput.focus();
});
