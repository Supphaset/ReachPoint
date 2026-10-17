import { useEffect, useRef, useState } from "react";
/** Smooth the displayed counter without requesting more board snapshots. */
export function useTween(target: number | undefined, duration = 450) {
  const [value, setValue] = useState(target);
  const current = useRef(target);
  useEffect(() => {
    if (target === undefined)
      return;
    const from = current.current ?? target;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      current.current = target;
      setValue(target);
      return;
    }
    const started = performance.now();
    let frame: number;
    function draw(now: number) {
      const progress = Math.min(1, (now - started) / duration);
      current.current = from + (target! - from) * progress;
      setValue(Math.round(current.current));
      if (progress < 1)
        frame = requestAnimationFrame(draw);
    }
    frame = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(frame);
  }, [target, duration]);
  return value;
}
