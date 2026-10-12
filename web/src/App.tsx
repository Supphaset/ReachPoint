import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./shell/AppShell";
import { BriefingPage } from "./features/briefing/BriefingPage";
import { JobsPage, WaitingPage } from "./features/team/TeamPages";
import { SplitPanel } from "./features/split/SplitPanel";
import { DeskPage } from "./features/desk/RisingWater";
import { DevUi } from "./pages/DevUi";
import { Home, Placeholder } from "./pages/Home";

/** Role routes. Team: /team/*; coordinator: /desk; resident: /status/:token; shared parts: /dev/ui. */
export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Home />} />
        <Route path="team/map/:areaId?/:zoneId?" element={<BriefingPage />} />
        <Route path="team/list" element={<WaitingPage />} />
        <Route path="team/mission" element={<JobsPage />} />
        <Route path="desk/split" element={<SplitPanel />} />
        <Route path="desk" element={<DeskPage />} />
        <Route path="call" element={<Placeholder title="Call" owner="your friend" day="Wed 14" />} />
        <Route path="status/:token" element={<Placeholder title="Request status" owner="your friend" day="Wed 14" />} />
        <Route path="dev/ui" element={<DevUi />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
