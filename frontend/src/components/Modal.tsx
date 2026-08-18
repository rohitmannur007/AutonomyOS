import { useEffect } from "react";
import { X } from "lucide-react";

export default function Modal({
  children,
  onClose,
  widthClass = "max-w-lg",
}: {
  children: React.ReactNode;
  onClose: () => void;
  widthClass?: string;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-ink-900/40 backdrop-blur-[1px] animate-fade-in"
        onClick={onClose}
      />
      <div
        className={`relative z-10 max-h-[90vh] w-full ${widthClass} overflow-y-auto rounded-xl border border-ink-200 bg-white shadow-popover animate-fade-in`}
      >
        <button
          onClick={onClose}
          className="absolute right-4 top-4 flex h-7 w-7 items-center justify-center rounded-md text-ink-400 hover:bg-ink-100 hover:text-ink-700"
        >
          <X className="h-4 w-4" />
        </button>
        {children}
      </div>
    </div>
  );
}
