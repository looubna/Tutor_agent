"use client";

import { levelGroups, programmes, type Level } from "@/lib/curriculum";
import { useT } from "@/lib/i18n";

/**
 * Programme first, then level. A subject taught to one syllabus — every
 * language, on the CEFR ladder — shows only the level menu. Maths is taught to
 * two, so it shows a programme menu above it, and picking a programme jumps to
 * that programme's first level.
 *
 * The chosen programme is read off the chosen level rather than kept in its own
 * state, so the two menus can never disagree.
 */
export function LevelMenu({
  id,
  levels,
  levelId,
  onChange,
  className = "",
}: {
  id: string;
  levels: Level[];
  levelId: string;
  onChange: (levelId: string) => void;
  className?: string;
}) {
  const t = useT();
  const runs = programmes(levels);
  const current = levels.find((l) => l.id === levelId) ?? levels[0];
  const run = runs.find((r) => r.name === current?.programme) ?? runs[0];
  if (!run) return null;

  const select =
    "w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm font-medium text-foreground outline-none focus:border-primary";

  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      {runs.length > 1 && (
        <>
          <label htmlFor={`${id}-programme`} className="sr-only">
            {t("book.programme")}
          </label>
          <select
            id={`${id}-programme`}
            value={run.name ?? ""}
            onChange={(e) => {
              const next = runs.find((r) => (r.name ?? "") === e.target.value);
              if (next?.levels[0]) onChange(next.levels[0].id);
            }}
            className={select}
          >
            {runs.map((r) => (
              <option key={r.name ?? ""} value={r.name ?? ""}>
                {r.name ?? t("book.level")}
              </option>
            ))}
          </select>
        </>
      )}

      <label htmlFor={id} className="sr-only">
        {t("book.level")}
      </label>
      <select
        id={id}
        value={current?.id ?? ""}
        onChange={(e) => onChange(e.target.value)}
        className={select}
      >
        {levelGroups(run.levels).map((group) =>
          group.group ? (
            <optgroup key={group.group} label={group.group}>
              {group.levels.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.label}
                </option>
              ))}
            </optgroup>
          ) : (
            group.levels.map((l) => (
              <option key={l.id} value={l.id}>
                {l.label}
              </option>
            ))
          ),
        )}
      </select>
    </div>
  );
}
