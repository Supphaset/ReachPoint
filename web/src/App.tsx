import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./shell/AppShell";
import { BriefingPage } from "./features/briefing/BriefingPage";
import { DevUi } from "./pages/DevUi";
import { Home, Placeholder } from "./pages/Home";

/** Role routes. Team: /team/*; coordinator: /desk; resident: /status/:token; shared parts: /dev/ui. */
export function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Home />} />
        <Route path="team/map/:areaId?/:zoneId?" element={<BriefingPage />} />
        <Route path="team/mission" element={<Placeholder title="My mission" owner="you" day="Wed 14" />} />
        <Route path="desk" element={<Placeholder title="Coordinator desk" owner="your friend" day="Tue 13" />} />
        <Route path="call" element={<Placeholder title="Call" owner="your friend" day="Wed 14" />} />
        <Route path="status/:token" element={<Placeholder title="Request status" owner="your friend" day="Wed 14" />} />
        <Route path="dev/ui" element={<DevUi />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
