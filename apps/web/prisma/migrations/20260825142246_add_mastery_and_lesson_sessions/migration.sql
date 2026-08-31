-- CreateTable
CREATE TABLE "Mastery" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "userId" TEXT NOT NULL,
    "skillId" TEXT NOT NULL,
    "score" REAL NOT NULL DEFAULT 0,
    "attempts" INTEGER NOT NULL DEFAULT 0,
    "correct" INTEGER NOT NULL DEFAULT 0,
    "streak" INTEGER NOT NULL DEFAULT 0,
    "halfLifeDays" REAL NOT NULL DEFAULT 1,
    "lastSeenAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "dueAt" DATETIME NOT NULL,
    "errorTags" TEXT NOT NULL DEFAULT '[]',
    CONSTRAINT "Mastery_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "LessonSession" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "bookingId" TEXT NOT NULL,
    "startedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "endedAt" DATETIME,
    "plan" TEXT,
    "finalState" TEXT,
    "summary" TEXT,
    "costCents" INTEGER,
    CONSTRAINT "LessonSession_bookingId_fkey" FOREIGN KEY ("bookingId") REFERENCES "Booking" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "LessonEvent" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "sessionId" TEXT NOT NULL,
    "at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "type" TEXT NOT NULL,
    "payload" TEXT NOT NULL DEFAULT '{}',
    CONSTRAINT "LessonEvent_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "LessonSession" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "ExerciseAttempt" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "sessionId" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "skillId" TEXT NOT NULL,
    "exerciseId" TEXT NOT NULL,
    "shown" TEXT NOT NULL,
    "expected" TEXT NOT NULL,
    "answer" TEXT NOT NULL,
    "correct" BOOLEAN NOT NULL,
    "latencyMs" INTEGER,
    "hintsUsed" INTEGER NOT NULL DEFAULT 0,
    "attemptNumber" INTEGER NOT NULL DEFAULT 1,
    "errorTag" TEXT,
    "at" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "ExerciseAttempt_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "LessonSession" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "ExerciseAttempt_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE INDEX "Mastery_userId_dueAt_idx" ON "Mastery"("userId", "dueAt");

-- CreateIndex
CREATE UNIQUE INDEX "Mastery_userId_skillId_key" ON "Mastery"("userId", "skillId");

-- CreateIndex
CREATE UNIQUE INDEX "LessonSession_bookingId_key" ON "LessonSession"("bookingId");

-- CreateIndex
CREATE INDEX "LessonEvent_sessionId_at_idx" ON "LessonEvent"("sessionId", "at");

-- CreateIndex
CREATE INDEX "ExerciseAttempt_sessionId_idx" ON "ExerciseAttempt"("sessionId");

-- CreateIndex
CREATE INDEX "ExerciseAttempt_userId_skillId_idx" ON "ExerciseAttempt"("userId", "skillId");
