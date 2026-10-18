/**
 * Demo room (api/server/rooms.py): each visitor gets their own copy of the demo, so two judges never see or undo
 * each other's work. The room comes from `?room=` (to open the same room on another phone), else this browser's
 * storage, else a new code. The /demo phones share it because they share storage and get it in their address.
 */
const KEY = "reachpoint.room";
const VALID = /^[A-Za-z0-9_-]{1,64}$/;
let fallback: string | null = null; // storage can be blocked (private windows); keep one code for this page

export function newRoomCode(random: () => number = Math.random): string {
  const letters = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"; // no 0/O, 1/I/L: easy to read out loud
  return Array.from({ length: 6 }, () => letters[Math.floor(random() * letters.length)]).join("");
}

export function demoRoom(search: string = typeof window === "undefined" ? "" : window.location.search): string {
  const fromUrl = new URLSearchParams(search).get("room");
  let stored: string | null = null;
  try {
    stored = window.localStorage.getItem(KEY);
  } catch {
    stored = fallback;
  }
  const room = fromUrl && VALID.test(fromUrl) ? fromUrl : stored && VALID.test(stored) ? stored : fallback ?? newRoomCode();
  fallback = room;
  try {
    if (room !== stored) window.localStorage.setItem(KEY, room);
  } catch {
    /* storage blocked: the code lives for this page only */
  }
  return room;
}

/** A link that opens this room on another device. */
export function roomLink(path: string, room: string): string {
  const origin = typeof window === "undefined" ? "" : window.location.origin;
  return `${origin}${path}?data=api&room=${encodeURIComponent(room)}`;
}
