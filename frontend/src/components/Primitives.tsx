import type { ReactNode } from "react";
import { Loader2, InboxIcon } from "lucide-react";

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex items-start justify-between gap-4">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-ink-900">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-ink-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Card({
  children,
  className = "",
  padded = true,
}: {
  children: ReactNode;
  className?: string;
  padded?: boolean;
}) {
  return (
    <div
      className={`rounded-xl border border-ink-200 bg-white shadow-card ${padded ? "p-5" : ""} ${className}`}
    >
      {children}
    </div>
  );
}

export function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-24 text-ink-400">
      <Loader2 className="h-5 w-5 animate-spin" />
      <div className="text-sm">{label}…</div>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  icon: Icon = InboxIcon,
}: {
  title: string;
  description?: string;
  icon?: typeof InboxIcon;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-20 text-center">
      <div className="mb-1 flex h-11 w-11 items-center justify-center rounded-full bg-ink-100 text-ink-400">
        <Icon className="h-5 w-5" strokeWidth={1.75} />
      </div>
      <div className="text-sm font-medium text-ink-700">{title}</div>
      {description && <div className="max-w-sm text-sm text-ink-400">{description}</div>}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
      <div className="text-sm font-medium text-escalate-text">Something went wrong</div>
      <div className="max-w-sm text-sm text-ink-400">{message}</div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-1 rounded-md border border-ink-200 bg-white px-3 py-1.5 text-xs font-medium text-ink-700 hover:bg-ink-50"
        >
          Try again
        </button>
      )}
    </div>
  );
}
