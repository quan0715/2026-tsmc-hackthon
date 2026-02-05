export function apiErrorMessage(error: unknown, fallback: string) {
  const err = error as {
    response?: { data?: { detail?: string }; status?: number };
    message?: string;
  }

  if (err?.response?.data?.detail) return err.response.data.detail
  if (err?.message) return err.message
  return fallback
}
