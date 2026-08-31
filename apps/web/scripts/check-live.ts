/**
 * Prove the spoken lesson actually works.
 *
 *   npm run check:live -- <bookingId>
 *
 * Type checks, lint and both unit suites pass whether or not the tutor ever
 * makes a sound — every real bug in this project's live path did exactly that.
 * This opens the agent's socket the way the browser does, waits for the tutor
 * to open the lesson, and reports how much audio came back.
 *
 * A healthy lesson greets unprompted within a couple of seconds and sends tens
 * of thousands of bytes of speech. Silence is the failure that looks identical
 * to a tutor still thinking.
 */
import { createHmac } from "node:crypto";
import { prisma } from "../src/lib/prisma";

async function main() {
  const bookingId = process.argv[2];
  if (!bookingId) {
    console.error("usage: npm run check:live -- <bookingId>");
    process.exit(2);
  }

  const secret = process.env.AGENT_TOKEN;
  const agent = process.env.AGENT_URL ?? "http://localhost:8080";
  if (!secret) {
    console.error("AGENT_TOKEN is not set; the agent will refuse the ticket.");
    process.exit(2);
  }

  const booking = await prisma.booking.findUnique({ where: { id: bookingId } });
  await prisma.$disconnect();
  if (!booking) {
    console.error(`No booking ${bookingId}. Run \`npm run lesson:now\` first.`);
    process.exit(2);
  }

  const expiry = Math.floor(Date.now() / 1000) + 120;
  const payload = `${bookingId}.${expiry}`;
  const signature = createHmac("sha256", secret).update(payload).digest("base64url");

  const socket = new WebSocket(`${agent.replace(/^http/, "ws")}/lesson/live`);
  const began = Date.now();
  const at = () => `+${((Date.now() - began) / 1000).toFixed(1)}s`;
  let frames = 0;
  let bytes = 0;
  let microphone: NodeJS.Timeout | undefined;

  socket.onopen = () => {
    socket.send(JSON.stringify({
      ticket: `${payload}.${signature}`,
      booking_id: bookingId,
      student_id: booking.studentId,
      subject: booking.subject,
      level_id: booking.level ?? "",
      item_id: `${booking.chapter ?? ""}.${booking.lesson ?? ""}`,
      start_time: new Date().toISOString(),
      duration_minutes: 50,
      language: "en-GB",
    }));
    // A browser streams the microphone continuously. Without it the model
    // finishes its turn and the session closes, which reads as a failure.
    microphone = setInterval(() => {
      if (socket.readyState === 1) socket.send(new Uint8Array(3200));
    }, 100);
  };

  socket.onmessage = (message: MessageEvent) => {
    const frame = JSON.parse(message.data as string);
    if (frame.type === "audio") {
      frames += 1;
      bytes += Math.floor(frame.data.length * 3 / 4);
      return;
    }
    if (frame.type === "transcript") {
      if (frame.final) console.log(`${at()} tutor: ${frame.text.slice(0, 70)}`);
    } else {
      console.log(`${at()} ${frame.type}`);
    }
  };

  setTimeout(() => {
    clearInterval(microphone);
    // 24kHz, 16-bit, mono: one second is 48,000 bytes.
    const seconds = bytes / 48_000;
    console.log(`\naudio: ${frames} frames, ${bytes} bytes = ${seconds.toFixed(1)}s of speech`);
    console.log(seconds > 1 ? "PASS — the tutor is teaching." : "FAIL — the tutor never spoke.");
    process.exit(seconds > 1 ? 0 : 1);
  }, 25_000);
}

main();
