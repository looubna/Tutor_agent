/**
 * Give every drawn icon a licence row.
 *
 *     npm run seed:icons
 *
 * §11 says every picture on a published deck has a recorded licence. Icons were
 * outside that rule while the only icons were the thirty-five drawn for this
 * course — obviously ours, so obviously fine. `find_pictogram` ends that: it
 * writes files from an outside icon set into the same directory, and a rule
 * with an exception in it is a rule that stops being checked.
 *
 * So the drawn set gets rows too, saying what it is. Idempotent: the asset
 * table is keyed on path, and anything already registered is left alone rather
 * than having its licence overwritten with "ours".
 */
import { readdirSync } from "node:fs";
import { join } from "node:path";

import { prisma } from "../src/lib/prisma";
import { ICON_URL_BASE, iconUrl } from "../src/lib/worksheet/boxes";

const DIR = join(process.cwd(), "public", ICON_URL_BASE.replace(/^\//, ""));

async function main() {
  const stems = readdirSync(DIR)
    .filter((f) => f.endsWith(".svg"))
    .map((f) => f.replace(/\.svg$/, ""));

  let added = 0;
  for (const stem of stems) {
    const path = iconUrl(stem);
    if (await prisma.asset.findUnique({ where: { path }, select: { id: true } })) continue;
    await prisma.asset.create({
      data: {
        path,
        source: "own-icon",
        licence: "Drawn for Zanoba — we hold the rights",
      },
    });
    added += 1;
  }

  console.log(`\n  ${stems.length} icons on disk · ${added} newly registered\n`);
}

main().catch((err) => { console.error(err.message); process.exit(1); });
