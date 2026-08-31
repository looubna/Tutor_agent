-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Booking" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "studentId" TEXT NOT NULL,
    "subject" TEXT NOT NULL,
    "level" TEXT,
    "chapter" TEXT,
    "kind" TEXT NOT NULL DEFAULT 'LESSON',
    "topic" TEXT,
    "startTime" DATETIME NOT NULL,
    "endTime" DATETIME NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'UPCOMING',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "googleEventId" TEXT,
    "reminderSentAt" DATETIME,
    CONSTRAINT "Booking_studentId_fkey" FOREIGN KEY ("studentId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);
INSERT INTO "new_Booking" ("chapter", "createdAt", "endTime", "googleEventId", "id", "kind", "level", "reminderSentAt", "startTime", "status", "studentId", "subject", "topic") SELECT "chapter", "createdAt", "endTime", "googleEventId", "id", "kind", "level", "reminderSentAt", "startTime", "status", "studentId", "subject", "topic" FROM "Booking";
DROP TABLE "Booking";
ALTER TABLE "new_Booking" RENAME TO "Booking";
CREATE INDEX "Booking_studentId_idx" ON "Booking"("studentId");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
