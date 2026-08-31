import { getCurrentUser } from "@/lib/dal";
import { prisma } from "@/lib/prisma";
import { isGoogleCalendarConfigured } from "@/lib/googleCalendar";
import { T } from "@/components/T";
import { HelpLanguagePicker } from "@/components/HelpLanguagePicker";

export default async function SettingsPage({
  searchParams,
}: {
  searchParams: Promise<{ connected?: string; error?: string }>;
}) {
  const { connected, error } = await searchParams;
  const user = await getCurrentUser();
  const configured = isGoogleCalendarConfigured();
  const connection = user
    ? await prisma.googleCalendarConnection.findUnique({ where: { userId: user.id } })
    : null;

  return (
    <div className="mx-auto max-w-2xl">
      <T k="settings.heading" as="h1" className="text-2xl font-semibold text-foreground font-display" />
      <T k="settings.subheading" as="p" className="mt-1 text-sm text-muted" />

      {connected && (
        <div className="mt-6 rounded-lg border border-primary/30 bg-primary-tint px-4 py-3 text-sm text-primary">
          <T k="settings.googleConnectedToast" />
        </div>
      )}
      {error && (
        <div className="mt-6 rounded-lg border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          <T k="settings.googleErrorToast" />
        </div>
      )}

      <div className="mt-8 rounded-xl border border-border bg-surface p-6 shadow-sm">
        <T k="settings.accountHeading" as="h2" className="text-sm font-semibold text-foreground font-display" />
        <p className="mt-2 text-sm text-foreground">{user?.name}</p>
        <p className="text-sm text-muted">{user?.email}</p>
      </div>

      <div className="mt-6 rounded-xl border border-border bg-surface p-6 shadow-sm">
        <T k="settings.helpLanguageHeading" as="h2" className="text-sm font-semibold text-foreground font-display" />
        <T k="settings.helpLanguageBody" as="p" className="mt-2 max-w-md text-sm text-muted" />
        <HelpLanguagePicker current={user?.supportLanguage ?? null} />
      </div>

      <div className="mt-6 rounded-xl border border-border bg-surface p-6 shadow-sm">
        <div className="flex items-start justify-between gap-4">
          <div>
            <T k="settings.googleHeading" as="h2" className="text-sm font-semibold text-foreground font-display" />
            <T k="settings.googleBody" as="p" className="mt-2 max-w-md text-sm text-muted" />
            <T k="settings.emailReminderNote" as="p" className="mt-2 text-xs text-muted" />
          </div>

          {connection ? (
            <div className="flex shrink-0 flex-col items-end gap-2">
              <span className="rounded-md bg-primary-tint px-2.5 py-1 text-xs font-medium text-primary">
                <T k="settings.googleConnected" />
              </span>
              <form action="/api/google-calendar/disconnect" method="POST">
                <button type="submit" className="text-xs font-medium text-muted hover:text-danger">
                  <T k="settings.googleDisconnect" />
                </button>
              </form>
            </div>
          ) : configured ? (
            <a
              href="/api/google-calendar/connect"
              className="shrink-0 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
            >
              <T k="settings.googleConnect" />
            </a>
          ) : (
            <span className="shrink-0 rounded-md bg-border px-2.5 py-1 text-xs font-medium text-muted">
              <T k="settings.googleNotConfigured" />
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
