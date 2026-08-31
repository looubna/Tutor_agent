/**
 * Fail with a sentence a person can act on.
 *
 * Prisma 7's CLI throws ERR_REQUIRE_ESM on Node 20, and better-sqlite3 is a
 * native module compiled for whichever Node installed it. Run anything here on
 * the wrong version and you get NODE_MODULE_VERSION 127 vs 115, which says
 * nothing about what to do next.
 */
const REQUIRED = 22;
const major = Number(process.versions.node.split(".")[0]);
if (major < REQUIRED) {
  console.error(
    `\n  This project needs Node ${REQUIRED} or newer. You are on ${process.versions.node}.\n\n` +
    `    nvm use            # reads .nvmrc\n` +
    `    nvm install 22     # if you do not have it yet\n\n` +
    `  Prisma 7 and better-sqlite3 both refuse to run on older Node, and the\n` +
    `  errors they give are about native module versions rather than this.\n`,
  );
  process.exit(1);
}
