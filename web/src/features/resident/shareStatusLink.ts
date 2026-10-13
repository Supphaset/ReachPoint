/** Keep the pre-written message with the link when native sharing is unavailable. */
export async function shareStatusLink(
  nav: { share?: (data: { url: string; text: string }) => Promise<void>; clipboard?: { writeText: (text: string) => Promise<void> } },
  url: string,
  text: string,
): Promise<"shared" | "copied" | "cancelled"> {
  if (nav.share) {
    try { await nav.share({ url, text }); return "shared"; }
    catch (error) {
      if (error instanceof Error && error.name === "AbortError") return "cancelled";
    }
  }
  if (!nav.clipboard) throw new Error("Clipboard unavailable");
  await nav.clipboard.writeText(`${text}\n${url}`);
  return "copied";
}
