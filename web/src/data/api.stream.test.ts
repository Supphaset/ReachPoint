import { afterEach, describe, expect, it, vi } from "vitest";
import { streamPost } from "./api";

afterEach(() => vi.unstubAllGlobals());

function respond(frames: string) {
  const bytes = new TextEncoder().encode(frames);
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(new ReadableStream({
    start(controller) {
      // Split every UTF-8 character and SSE delimiter across reads.
      for (const byte of bytes) controller.enqueue(new Uint8Array([byte]));
      controller.close();
    },
  }), { headers: { "Content-Type": "text/event-stream" } })));
}

describe("streamPost", () => {
  it("delivers Thai deltas before the snapshot across fragmented UTF-8 and CRLF frames", async () => {
    respond('event: status\r\ndata: {"phase":"reading"}\r\n\r\nevent: delta\r\ndata: {"text":"น้ำสูง"}\r\n\r\nevent: delta\ndata: {"text":"ถึงไหนคะ?"}\n\nevent: snapshot\ndata: {"revision":1}\n\n');
    const deltas: string[] = [];
    expect(await streamPost("/synthetic", {}, (text) => deltas.push(text))).toEqual({ revision: 1 });
    expect(deltas).toEqual(["น้ำสูง", "ถึงไหนคะ?"]);
    expect(fetch).toHaveBeenCalledWith("/synthetic", expect.objectContaining({
      headers: expect.objectContaining({ Accept: "text/event-stream" }),
    }));
  });

  it("surfaces errors after stream headers without accepting an incomplete turn", async () => {
    respond('event: status\ndata: {"phase":"reading"}\n\nevent: error\ndata: {"message":"Please retry","status":503}\n\n');
    await expect(streamPost("/synthetic", {}, vi.fn())).rejects.toMatchObject({ message: "Please retry", status: 503 });
  });

  it("rejects a connection lost after a partial reply", async () => {
    respond('event: delta\ndata: {"text":"น้ำสูง"}\n\n');
    await expect(streamPost("/synthetic", {}, vi.fn())).rejects.toMatchObject({ code: "STREAM" });
  });
});
