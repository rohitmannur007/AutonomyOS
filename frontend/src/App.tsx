import { BrowserRouter, Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Dashboard from "./pages/Dashboard";
import TicketInbox from "./pages/TicketInbox";
import TicketInvestigation from "./pages/TicketInvestigation";
import Analytics from "./pages/Analytics";
import KnowledgeBase from "./pages/KnowledgeBase";

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen w-full overflow-hidden bg-ink-50">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-[1240px] px-8 py-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/tickets" element={<TicketInbox />} />
              <Route path="/tickets/:id" element={<TicketInvestigation />} />
              <Route path="/knowledge" element={<KnowledgeBase />} />
              <Route path="/analytics" element={<Analytics />} />
            </Routes>
          </div>
        </main>
      </div>
    </BrowserRouter>
  );
}
