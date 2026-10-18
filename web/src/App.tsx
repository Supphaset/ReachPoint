import { UiLangProvider } from "./features/v2/ui/lang";
import { Navigate, Route, Routes } from "react-router-dom";
import { OverviewLanding } from "./features/v2/OverviewLanding";
import { V2Page } from "./features/v2/V2Page";
import { CasePage } from "./features/v2/volunteer/CasePage";
import { FeedPage } from "./features/v2/volunteer/FeedPage";
import { OverviewPage } from "./features/v2/volunteer/OverviewPage";
import { TripPage } from "./features/v2/volunteer/TripPage";
import { MissionPage } from "./features/v2/volunteer/MissionPage";
import { ZonePage } from "./features/v2/volunteer/ZonePage";
/** V2 overview, family intake and volunteer routes. */
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
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes></UiLangProvider>
  );
}
