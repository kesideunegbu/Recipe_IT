"""Password hashing for Recipe_IT.

Uses Argon2id (OWASP's recommended algorithm for password storage).
The hash string it produces contains the algorithm, its settings, and a random
salt, so it is the ONLY thing that needs to be stored in the database. Never
store or log the plain-text password.
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

# Library defaults follow RFC 9106's recommended settings. One shared instance
# is fine; it is thread-safe.
_hasher = PasswordHasher()

MIN_PASSWORD_LENGTH = 8
# Cap length so someone can't make the server hash a multi-megabyte "password".
MAX_PASSWORD_LENGTH = 128


def validate_password(password):
    """Return an error message if the password is not acceptable, else None."""
    if not isinstance(password, str):
        return "Password must be a string."
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if len(password) > MAX_PASSWORD_LENGTH:
        return f"Password must be at most {MAX_PASSWORD_LENGTH} characters."
    return None


def hash_password(password):
    """Hash a plain-text password. Store the returned string in the database."""
    error = validate_password(password)
    if error:
        raise ValueError(error)
    return _hasher.hash(password)


def verify_password(stored_hash, password):
    """Return True if the password matches the stored hash, False otherwise."""
    if not isinstance(password, str) or len(password) > MAX_PASSWORD_LENGTH:
        return False
    try:
        return _hasher.verify(stored_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def needs_rehash(stored_hash):
    """True if the hash was made with older settings and should be updated.

    Call this after a successful login; if True, hash the password again and
    save the new hash. This lets us strengthen settings later without
    forcing everyone to reset their password.
    """
    return _hasher.check_needs_rehash(stored_hash)
