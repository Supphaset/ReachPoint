/** Playback follows wall time, independently of outstanding API requests. */
export function replayHours(from: number, to: number, steps = 40): number[] {
  return Array.from({ length: steps + 1 }, (_, index) => from + (to - from) * index / steps);
}

export function playFlood(from: number, to: number, duration: number, tick: (hour: number) => void, done: () => void) {
  const hours = replayHours(from, to);
  const started = performance.now();
  let lastStep = -1;
  let timer: ReturnType<typeof setTimeout>;
  let cancelled = false;
  function advance() {
    if (cancelled)
      return;
    const elapsed = performance.now() - started;
    const step = Math.min(hours.length - 1, Math.floor(elapsed / duration * (hours.length - 1)));
    if (step !== lastStep) {
      lastStep = step;
      tick(hours[step]);
    }
    if (elapsed >= duration) {
      done();
      return;
    }
    // Skip missed steps after a busy frame instead of extending the replay.
    timer = setTimeout(advance, Math.max(0, started + (step + 1) * duration / (hours.length - 1) - performance.now()));
  }
  advance();
  return () => {
    cancelled = true;
    clearTimeout(timer);
  };
}
/** A snapshot updates the view when it is newer than the last one shown, so a slow server still shows the flood
 * rising during the replay instead of freezing until the end; invalidation (Skip, unmount) drops everything older. */
export function latestRequest<Value>(accept: (value: Value) => void, reject: (reason: unknown) => void) {
  let version = 0;
  let shown = 0;
  let floor = 0;
  return {
    load(request: () => Promise<Value>) {
      const requestedVersion = ++version;
      void request().then(value => {
        if (requestedVersion > shown && requestedVersion > floor) {
          shown = requestedVersion;
          accept(value);
        }
      }, reason => {
        if (requestedVersion === version) reject(reason);
      });
    },
    invalidate() {
      floor = ++version;
    },
  };
}
