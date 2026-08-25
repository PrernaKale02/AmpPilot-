/**
 * Auth actions for the MVP.
 *
 * Both resolve immediately today; they'll call the FastAPI auth endpoints
 * later without any change to how screens use them.
 */

export async function signInWithGoogle() {
  // TODO: replace with real Google OAuth sign-in once auth is integrated.
  return { success: true };
}

export async function continueAsGuest() {
  // TODO: replace with real guest session handling once auth is integrated.
  return { success: true };
}
