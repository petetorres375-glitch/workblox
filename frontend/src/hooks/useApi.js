import { useState } from "react";

export function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [errorCode, setErrorCode] = useState(null);

  async function call(fn) {
    setLoading(true);
    setError(null);
    setErrorCode(null);
    try {
      return await fn();
    } catch (err) {
      setError(err.message);
      setErrorCode(err.code || null);
      return null;
    } finally {
      setLoading(false);
    }
  }

  return { loading, error, errorCode, call };
}
