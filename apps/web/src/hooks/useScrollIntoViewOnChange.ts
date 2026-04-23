import { RefObject, useEffect } from "react";

export function useScrollIntoViewOnChange<T>(
  targetRef: RefObject<HTMLElement | null>,
  value: T | null | undefined,
) {
  useEffect(() => {
    if (!value || !targetRef.current) {
      return;
    }

    const frameId = window.requestAnimationFrame(() => {
      targetRef.current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });

    return () => {
      window.cancelAnimationFrame(frameId);
    };
  }, [targetRef, value]);
}
