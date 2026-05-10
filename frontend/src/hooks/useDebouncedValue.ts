import { useEffect, useState } from "react";

/** 값이 안정될 때까지 delayMs 대기 후 갱신. 검색·자동평가 등 throttling 용. */
export function useDebouncedValue<T>(value: T, delayMs = 500): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(t);
  }, [value, delayMs]);
  return debounced;
}
