-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_LessonSession" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "bookingId" TEXT NOT NULL,
    "startedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "endedAt" DATETIME,
    "plan" TEXT,
    "finalState" TEXT,
    "summary" TEXT,
    "costCents" INTEGER,
    "openExerciseId" TEXT,
    "openExerciseAt" DATETIME,
    "openExerciseHints" INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT "LessonSession_bookingId_fkey" FOREIGN KEY ("bookingId") REFERENCES "Booking" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);
INSERT INTO "new_LessonSession" ("bookingId", "costCents", "endedAt", "finalState", "id", "plan", "startedAt", "summary") SELECT "bookingId", "costCents", "endedAt", "finalState", "id", "plan", "startedAt", "summary" FROM "LessonSession";
DROP TABLE "LessonSession";
ALTER TABLE "new_LessonSession" RENAME TO "LessonSession";
CREATE UNIQUE INDEX "LessonSession_bookingId_key" ON "LessonSession"("bookingId");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
