import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./shell/AppShell";
import { BriefingPage } from "./features/briefing/BriefingPage";
import { JobsPage, WaitingPage } from "./features/team/TeamPages";
import { SplitPanel } from "./features/split/SplitPanel";
import { DeskPage } from "./features/desk/RisingWater";
import { CallPage } from "./features/intake/CallPage";
import { StatusPage } from "./features/resident/StatusPage";
import { DevUi } from "./pages/DevUi";
import { FloodPage } from "./features/flood/FloodPage";
import { Home } from "./pages/Home";
import { DemoPage } from "./features/demo/DemoPage";
import { V2Page } from "./features/v2/V2Page";

/** v2 judge page at /. The earlier role screens stay reachable from /classic. Role routes. Team: /team/*; coordinator: /desk; resident: /status/:token; shared parts: /dev/ui. */
export function App() {
  return (
    <Routes>
      <Route index element={<V2Page />} />
      <Route path="demo" element={<DemoPage />} />
      <Route element={<AppShell />}>
        <Route path="classic" element={<Home />} />
        <Route path="team/map/:areaId?/:zoneId?" element={<BriefingPage />} />
        <Route path="team/list" element={<WaitingPage />} />
        <Route path="team/mission" element={<JobsPage />} />
        <Route path="desk/map" element={<FloodPage />} />
        <Route path="desk/split" element={<SplitPanel />} />
        <Route path="desk" element={<DeskPage />} />
        <Route path="call" element={<CallPage />} />
        <Route path="status/:token" element={<StatusPage />} />
        <Route path="dev/ui" element={<DevUi />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
