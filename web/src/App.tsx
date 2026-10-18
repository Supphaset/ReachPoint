import { UiLangProvider } from "./features/v2/ui/lang";
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
import { OverviewLanding } from "./features/v2/OverviewLanding";
import { V2Page } from "./features/v2/V2Page";
import { CasePage } from "./features/v2/volunteer/CasePage";
import { FeedPage } from "./features/v2/volunteer/FeedPage";
import { OverviewPage } from "./features/v2/volunteer/OverviewPage";
import { TripPage } from "./features/v2/volunteer/TripPage";
import { MissionPage } from "./features/v2/volunteer/MissionPage";
import { ZonePage } from "./features/v2/volunteer/ZonePage";
/** v2 judge page at /; volunteer pages at /v (docs/product/v2-volunteer-pages.md). The earlier role screens stay reachable from /classic. Role routes. Team: /team/*; coordinator: /desk; resident: /status/:token; shared parts: /dev/ui. */
export function App() {
  return (
    <UiLangProvider><Routes>
      <Route index element={<OverviewLanding />} />
      <Route path="report" element={<V2Page />} />
      <Route path="v" element={<OverviewPage />} />
      <Route path="v/feed" element={<FeedPage />} />
      <Route path="v/mission/:zoneId" element={<MissionPage />} />
      <Route path="v/zone/:id" element={<ZonePage />} />
      <Route path="v/case/:id" element={<CasePage />} />
      <Route path="v/plan/legacy" element={<TripPage />} />
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
    </Routes></UiLangProvider>
  );
}
