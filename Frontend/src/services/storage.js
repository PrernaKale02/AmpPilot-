const memoryStore = new Map();

/**
 * Minimal key-value storage used by feature services.
 *
 * Backed by an in-memory map for the MVP. Swap the implementation for
 * AsyncStorage/SecureStore later without changing any calling code.
 */
export const storage = {
  async getItem(key) {
    return memoryStore.has(key) ? memoryStore.get(key) : null;
  },
  async setItem(key, value) {
    memoryStore.set(key, value);
  },
  async removeItem(key) {
    memoryStore.delete(key);
  },
};
