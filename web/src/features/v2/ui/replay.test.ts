import { afterEach, describe, expect, it, vi } from "vitest";
import { latestRequest, playFlood, replayHours } from "./replay";
function deferred<Value>() {
  let resolve!: (value: Value) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<Value>((accept, fail) => {
    resolve = accept;
    reject = fail;
  });
  return { promise, resolve, reject };
}
afterEach(() => vi.useRealTimers());
describe("replay scheduler", () => {
  it("precomputes 40 equal steps from 21 Nov 06:00 (hour zero) to demo now", () => {
    const hours = replayHours(0, 96);
    expect(hours).toHaveLength(41);
    expect(hours[0]).toBe(0);
    expect(hours[20]).toBe(48);
    expect(hours[40]).toBe(96);
  });
  it("finishes at 20 seconds even when every API request is still pending", () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "performance"] });
    const requests: number[] = [];
    const accepted = vi.fn();
    const loader = latestRequest(accepted, vi.fn());
    const done = vi.fn(() => loader.invalidate());
    playFlood(0, 96, 20000, hour => {
      requests.push(hour);
      loader.load(() => new Promise(() => undefined));
    }, done);
    vi.advanceTimersByTime(19999);
    expect(done).not.toHaveBeenCalled();
    vi.advanceTimersByTime(1);
    expect(done).toHaveBeenCalledOnce();
    expect(requests).toEqual(replayHours(0, 96));
    expect(accepted).not.toHaveBeenCalled();
  });
  it("drops late snapshots and stale errors; Skip invalidates pending requests", async () => {
    const accepted = vi.fn();
    const rejected = vi.fn();
    const loader = latestRequest<number>(accepted, rejected);
    const old = deferred<number>();
    const recent = deferred<number>();
    loader.load(() => old.promise);
    loader.load(() => recent.promise);
    recent.resolve(20);
    await Promise.resolve();
    old.resolve(10);
    await Promise.resolve();
    expect(accepted.mock.calls).toEqual([[20]]);
    const pending = deferred<number>();
    loader.load(() => pending.promise);
    loader.invalidate();
    pending.reject(new Error("old request"));
    await Promise.resolve();
    expect(rejected).not.toHaveBeenCalled();
  });
  it("shows each snapshot that is newer than the one on screen, so a slow server still animates", async () => {
    const accepted = vi.fn();
    const loader = latestRequest<number>(accepted, vi.fn());
    const first = deferred<number>();
    const second = deferred<number>();
    loader.load(() => first.promise);
    loader.load(() => second.promise);
    first.resolve(10);
    await Promise.resolve();
    second.resolve(20);
    await Promise.resolve();
    expect(accepted.mock.calls).toEqual([[10], [20]]);
  });
  it("cancels future ticks and completion on Skip or unmount", () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "performance"] });
    const tick = vi.fn();
    const done = vi.fn();
    const cancel = playFlood(0, 96, 20000, tick, done);
    vi.advanceTimersByTime(500);
    cancel();
    vi.advanceTimersByTime(30000);
    expect(tick).toHaveBeenCalledTimes(2);
    expect(done).not.toHaveBeenCalled();
  });
});
