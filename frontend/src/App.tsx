import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { AgentPage } from "./pages/AgentPage";
import { LibraryPage } from "./pages/LibraryPage";
import { ScanPage } from "./pages/ScanPage";
import { SettingsPage } from "./pages/SettingsPage";
import { TagPicturesPage } from "./pages/TagPicturesPage";
import { PicturePage } from "./pages/PicturePage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/library" replace />} />
        <Route path="/library" element={<LibraryPage />} />
        <Route path="/scan" element={<ScanPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/agent/:sessionId?" element={<AgentPage />} />
        <Route path="/tags/:tagId/pictures" element={<TagPicturesPage />} />
        <Route path="/pictures/:pictureId" element={<PicturePage />} />
        <Route path="*" element={<Navigate to="/library" replace />} />
      </Route>
    </Routes>
  );
}
