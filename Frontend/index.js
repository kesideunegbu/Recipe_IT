
// Main page: collect ingredients, ask the backend for recipes, show them.
// Recipe text is always inserted with textContent (never innerHTML), so
// nothing in a Gemini reply can run as code on this page.

const MAX_INGREDIENTS = 30;

const form = document.getElementById("generate-form");
const chipBox = document.getElementById("chip-box");
const chipList = document.getElementById("chips");
const input = document.getElementById("ingredient-input");
const servingsSelect = document.getElementById("servings");
const minutesSelect = document.getElementById("max-minutes");
const generateButton = document.getElementById("generate-btn");
const status = document.getElementById("status");
const results = document.getElementById("results");
const template = document.getElementById("recipe-template");

const ingredients = [];

function setStatus(text, kind) {
    status.textContent = text;
    status.className = kind || "";
}

function renderChips() {
    chipList.replaceChildren();
    ingredients.forEach(function (name, index) {
        const chip = document.createElement("li");
        chip.className = "chip";
        chip.textContent = name;

        const remove = document.createElement("button");
        remove.type = "button";
        remove.textContent = "×";
        remove.setAttribute("aria-label", "Remove " + name);
        remove.addEventListener("click", function () {
            ingredients.splice(index, 1);
            renderChips();
            input.focus();
        });

        chip.appendChild(remove);
        chipList.appendChild(chip);
    });
}

// Add whatever is typed (split on commas). Returns false if nothing was added.
function addTyped() {
    const parts = input.value.split(",");
    let added = false;
    for (const part of parts) {
        const name = part.trim().toLowerCase().replace(/\s+/g, " ");
        if (!name || ingredients.includes(name)) {
            continue;
        }
        if (ingredients.length >= MAX_INGREDIENTS) {
            setStatus("You can add up to " + MAX_INGREDIENTS + " ingredients.", "error");
            break;
        }
        ingredients.push(name);
        added = true;
    }
    input.value = "";
    renderChips();
    return added;
}

input.addEventListener("keydown", function (event) {
    if (event.key === "Enter" || event.key === ",") {
        event.preventDefault();
        addTyped();
    } else if (event.key === "Backspace" && !input.value && ingredients.length) {
        ingredients.pop();
        renderChips();
    }
});

// Clicking anywhere in the box focuses the text field.
chipBox.addEventListener("click", function (event) {
    if (event.target === chipBox) {
        input.focus();
    }
});

function renderRecipes(recipes) {
    results.replaceChildren();
    for (const recipe of recipes) {
        const card = template.content.firstElementChild.cloneNode(true);
        card.querySelector(".card-title").textContent = recipe.title;

        const meta = [];
        if (recipe.prep_minutes) meta.push(recipe.prep_minutes + " min");
        if (recipe.servings) meta.push("serves " + recipe.servings);
        card.querySelector(".card-meta").textContent = meta.join(" · ");
        card.querySelector(".card-description").textContent = recipe.description;

        const ingredientList = card.querySelector(".card-ingredients");
        for (const item of recipe.ingredients) {
            const li = document.createElement("li");
            li.textContent = (item.amount ? item.amount + " " : "") + item.name;
            if (!item.in_pantry) {
                const need = document.createElement("span");
                need.className = "need";
                need.textContent = "need to buy";
                li.appendChild(need);
            }
            ingredientList.appendChild(li);
        }

        const stepList = card.querySelector(".card-steps");
        for (const step of recipe.steps) {
            const li = document.createElement("li");
            li.textContent = step;
            stepList.appendChild(li);
        }

        results.appendChild(card);
    }
}

form.addEventListener("submit", async function (event) {
    event.preventDefault();
    addTyped(); // include anything typed but not yet turned into a chip

    if (!ingredients.length) {
        setStatus("Add at least one ingredient first.", "error");
        input.focus();
        return;
    }

    const body = {
        ingredients: ingredients,
        servings: Number(servingsSelect.value),
    };
    if (minutesSelect.value) {
        body.max_minutes = Number(minutesSelect.value);
    }

    generateButton.disabled = true;
    const started = Date.now();
    setStatus("Cooking up recipes…", "loading");
    // Show elapsed time so a slow reply doesn't look frozen.
    const timer = setInterval(function () {
        const seconds = Math.round((Date.now() - started) / 1000);
        setStatus("Cooking up recipes… " + seconds + "s", "loading");
    }, 1000);

    try {
        const response = await fetch("/api/recipes/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });

        if (response.status === 401) {
            window.location.href = "login.html";
            return;
        }

        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            setStatus(data.error || "Something went wrong. Please try again.", "error");
            return;
        }

        renderRecipes(data.recipes);
        const seconds = ((Date.now() - started) / 1000).toFixed(1);
        setStatus(data.recipes.length + " recipes in " + seconds + "s", "");
    } catch (error) {
        setStatus("Could not reach the server. Please try again.", "error");
    } finally {
        clearInterval(timer);
        generateButton.disabled = false;
    }
});
