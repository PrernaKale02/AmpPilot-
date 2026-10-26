const PREFIX = "[AI Voice Assistant]";

function describeError(error) {
  if (error instanceof Error) {
    return { errorName: error.name, errorMessage: error.message };
  }
  if (typeof error === "string") {
    return { errorMessage: error };
  }
  return { errorMessage: "Unknown error" };
}

export function logAssistantError(stage, error, details = {}) {
  console.error(PREFIX, {
    level: "error",
    stage,
    ...details,
    ...describeError(error),
  });
}

export function logAssistantWarning(stage, details = {}) {
  console.warn(PREFIX, {
    level: "warning",
    stage,
    ...details,
  });
}
