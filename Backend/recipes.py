"""Recipe endpoints. For now: generate recipes from a list of ingredients.

Saving, listing and favouriting recipes come once the database tables exist.
"""

import math

from flask import Blueprint, current_app, g, jsonify, request

from auth import login_required
from generator import GenerationError

bp = Blueprint("recipes", __name__, url_prefix="/api/recipes")

MAX_INGREDIENTS = 30
MAX_INGREDIENT_LENGTH = 50
# Letters in any language, digits, spaces and a little punctuation
# ("half-and-half", "baker's yeast", "salt & pepper", "1/2 lemon").
_ALLOWED_PUNCTUATION = set(" -'&,./()")


def _clean_ingredients(value):
    """Return (ingredients, error_message)."""
    if not isinstance(value, list) or not value:
        return None, "Add at least one ingredient."
    if len(value) > MAX_INGREDIENTS:
        return None, f"Use at most {MAX_INGREDIENTS} ingredients."

    cleaned = []
    for item in value:
        if not isinstance(item, str):
            return None, "Each ingredient must be text."
        name = " ".join(item.split()).lower()
        if not name:
            continue
        if len(name) > MAX_INGREDIENT_LENGTH:
            return None, f"Ingredient names can be at most {MAX_INGREDIENT_LENGTH} characters."
        if not all(ch.isalnum() or ch in _ALLOWED_PUNCTUATION for ch in name):
            return None, f"\"{name}\" contains characters that aren't allowed."
        if name not in cleaned:
            cleaned.append(name)

    if not cleaned:
        return None, "Add at least one ingredient."
    return cleaned, None


def _optional_int(data, key, low, high, default):
    """Return (value, error_message) for an optional whole-number field."""
    value = data.get(key, default)
    if value is None:
        return default, None
    # bool is a subclass of int in Python; reject true/false explicitly.
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        return None, f"{key} must be a whole number from {low} to {high}."
    return value, None


def _slow_down_message(wait):
    if wait < 90:
        when = f"{wait} second{'s' if wait != 1 else ''}"
    elif wait < 90 * 60:
        when = f"{math.ceil(wait / 60)} minutes"
    else:
        when = f"{math.ceil(wait / 3600)} hours"
    return f"You're making recipes too quickly. Try again in {when}."


@bp.post("/generate")
@login_required
def generate():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Send the ingredients as JSON."), 400

    ingredients, error = _clean_ingredients(data.get("ingredients"))
    if error:
        return jsonify(error=error), 400
    servings, error = _optional_int(data, "servings", 1, 12, default=2)
    if error:
        return jsonify(error=error), 400
    max_minutes, error = _optional_int(data, "max_minutes", 5, 240, default=None)
    if error:
        return jsonify(error=error), 400

    generator = current_app.extensions.get("recipe_generator")
    if generator is None:
        return jsonify(error="Recipe generation is not available right now."), 503

    # Checked after validation, so bad input never uses up a user's allowance.
    allowed, wait = current_app.extensions["generate_limiter"].hit(g.user_id)
    if not allowed:
        response = jsonify(error=_slow_down_message(wait))
        response.headers["Retry-After"] = str(wait)
        return response, 429

    try:
        recipes, model = generator.generate(ingredients, servings, max_minutes)
    except GenerationError as exc:
        return jsonify(error=exc.message), exc.status

    return jsonify(recipes=recipes, ingredients=ingredients, model=model), 200
