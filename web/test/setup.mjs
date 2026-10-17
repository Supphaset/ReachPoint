import { webcrypto } from "node:crypto";

// Node 18 test workers need the browser API used for submission IDs.
if (!globalThis.crypto) Object.defineProperty(globalThis, "crypto", { value: webcrypto, configurable: true });
