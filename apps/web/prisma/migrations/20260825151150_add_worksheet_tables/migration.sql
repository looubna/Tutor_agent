-- CreateTable
CREATE TABLE "LessonSpec" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "lessonId" TEXT NOT NULL,
    "version" INTEGER NOT NULL DEFAULT 1,
    "status" TEXT NOT NULL DEFAULT 'DRAFT',
    "approvedBy" TEXT,
    "approvedAt" DATETIME,
    "body" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- CreateTable
CREATE TABLE "LessonDoc" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "lessonId" TEXT NOT NULL,
    "version" INTEGER NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'DRAFT',
    "publishedBy" TEXT,
    "publishedAt" DATETIME,
    "specId" TEXT,
    "boxes" TEXT NOT NULL,
    "builtBy" TEXT,
    "costCents" INTEGER,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "LessonDoc_specId_fkey" FOREIGN KEY ("specId") REFERENCES "LessonSpec" ("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Asset" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "docId" TEXT,
    "path" TEXT NOT NULL,
    "kind" TEXT NOT NULL DEFAULT 'image',
    "source" TEXT NOT NULL,
    "licence" TEXT NOT NULL,
    "credit" TEXT,
    "sourceUrl" TEXT,
    "prompt" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Asset_docId_fkey" FOREIGN KEY ("docId") REFERENCES "LessonDoc" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "StudentLessonDoc" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "bookingId" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "docId" TEXT NOT NULL,
    "docVersion" INTEGER NOT NULL,
    "ops" TEXT NOT NULL DEFAULT '[]',
    "extraPractice" TEXT,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "StudentLessonDoc_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User" ("id") ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT "StudentLessonDoc_docId_fkey" FOREIGN KEY ("docId") REFERENCES "LessonDoc" ("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- CreateIndex
CREATE UNIQUE INDEX "LessonSpec_lessonId_version_key" ON "LessonSpec"("lessonId", "version");

-- CreateIndex
CREATE INDEX "LessonDoc_lessonId_status_idx" ON "LessonDoc"("lessonId", "status");

-- CreateIndex
CREATE UNIQUE INDEX "LessonDoc_lessonId_version_key" ON "LessonDoc"("lessonId", "version");

-- CreateIndex
CREATE UNIQUE INDEX "Asset_path_key" ON "Asset"("path");

-- CreateIndex
CREATE INDEX "StudentLessonDoc_userId_idx" ON "StudentLessonDoc"("userId");

-- CreateIndex
CREATE UNIQUE INDEX "StudentLessonDoc_bookingId_key" ON "StudentLessonDoc"("bookingId");
