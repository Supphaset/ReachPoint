import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { Bubble, GeminiReceipt } from "./ChatShell";

describe("chat receipts", () => {
  it("renders returned facts with a public reader label and linked turn", () => {
    const html = renderToStaticMarkup(<GeminiReceipt turn={3} reader="gemini-live" facts={[
      { field: "people", value: 2, quote: "อยู่กับแม่" },
      { field: "depthRange", value: [0.7, 1.2], quote: "น้ำถึงเอว" },
    ]} extra="โซน B5" />);
    expect(html).toContain('data-turn="3"');
    expect(html).toContain("Gemini");
    expect(html).toContain("0.7–1.2 m");
    expect(html).toContain("โซน B5");
    expect(renderToStaticMarkup(<GeminiReceipt reader="stand-in" facts={[]} />)).toContain("Rules");
    expect(html).not.toContain("Understood");
  });
  it("does not claim a pending message was read or invent its time", () => {
    const pending = renderToStaticMarkup(<Bubble person>ทดสอบ</Bubble>);
    expect(pending).not.toContain("Read");
    expect(pending).not.toContain("<time");
    const read = renderToStaticMarkup(<Bubble person read at="06:12">ทดสอบ</Bubble>);
    expect(read).toContain("Read");
    expect(read).toContain("06:12");
  });
});
