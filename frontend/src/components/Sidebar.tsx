import { NavLink } from "react-router-dom";
import { LayoutGrid, Inbox, BarChart3, BookOpen, Bot } from "lucide-react";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutGrid, end: true },
  { to: "/tickets", label: "Ticket Inbox", icon: Inbox },
  { to: "/knowledge", label: "Knowledge Base", icon: BookOpen },
  { to: "/analytics", label: "Autonomy Analytics", icon: BarChart3 },
];

export default function Sidebar() {
  return (
    <aside className="flex h-full w-60 shrink-0 flex-col border-r border-ink-200 bg-white">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-ink-900">
          <Bot className="h-4.5 w-4.5 text-auto" strokeWidth={2.2} />
        </div>
        <div className="leading-tight">
          <div className="text-[15px] font-semibold tracking-tight text-ink-900">AutonomyOS</div>
          <div className="text-[11px] font-medium uppercase tracking-wider text-ink-400">
            AI Operations
          </div>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-0.5 px-3">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `group flex items-center gap-2.5 rounded-md px-3 py-2 text-[13.5px] font-medium transition-colors ${
                isActive
                  ? "bg-ink-900 text-white"
                  : "text-ink-600 hover:bg-ink-100 hover:text-ink-900"
              }`
            }
          >
            <item.icon className="h-[17px] w-[17px] shrink-0" strokeWidth={2} />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-ink-100 px-4 py-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-ink-100 text-[12px] font-semibold text-ink-600">
            OM
          </div>
          <div className="leading-tight">
            <div className="text-[13px] font-medium text-ink-800">Operations Manager</div>
            <div className="text-[11px] text-ink-400">MSP Support Desk</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
