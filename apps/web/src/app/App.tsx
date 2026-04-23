import { useState } from "react";

import { TabNav } from "../components/ui/TabNav";
import { CampaignAnalysisTab } from "../features/campaign-analysis/components/CampaignAnalysisTab";
import { ImagePromptTab } from "../features/image-prompt/components/ImagePromptTab";
import { KnowledgeBaseTab } from "../features/knowledge-base/components/KnowledgeBaseTab";
import { PublicationGeneratorTab } from "../features/publication-generator/components/PublicationGeneratorTab";
import {
  getWorkspacePanelId,
  getWorkspaceTabId,
  workspaceTabs,
  type WorkspaceTabId,
} from "./workspaceTabs";

function renderWorkspaceTab(tabId: WorkspaceTabId) {
  switch (tabId) {
    case "campaign-analysis":
      return <CampaignAnalysisTab />;
    case "publication-generator":
      return <PublicationGeneratorTab />;
    case "knowledge-base-qa":
      return <KnowledgeBaseTab />;
    case "image-prompt":
      return <ImagePromptTab />;
    default:
      return null;
  }
}

export default function App() {
  const [activeTab, setActiveTab] = useState<WorkspaceTabId>("campaign-analysis");
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  return (
    <div className={`shell app-shell ${isSidebarCollapsed ? "is-sidebar-collapsed" : ""}`}>
      <aside className="app-sidebar" aria-label="Primary navigation">
        <div className="sidebar-brand" aria-label="OneBotAds">
          <span className="sidebar-logo" aria-hidden="true">O</span>
          <span className="sidebar-brand-name">OneBotAds</span>
        </div>

        <TabNav
          tabs={workspaceTabs}
          activeTab={activeTab}
          isCollapsed={isSidebarCollapsed}
          onChange={setActiveTab}
        />

        <button
          className="sidebar-toggle"
          type="button"
          aria-label={isSidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          aria-expanded={!isSidebarCollapsed}
          onClick={() => setIsSidebarCollapsed((current) => !current)}
        >
          <svg className="sidebar-toggle-icon" viewBox="0 0 20 20" aria-hidden="true" focusable="false">
            <path d="M12.8 4.8 7.6 10l5.2 5.2" />
          </svg>
          <span className="sidebar-toggle-label">Collapse</span>
        </button>
      </aside>

      <main className="workspace workspace-single">
        <section
          id={getWorkspacePanelId(activeTab)}
          className="workspace-panel tabpanel"
          role="tabpanel"
          aria-labelledby={getWorkspaceTabId(activeTab)}
        >
          {renderWorkspaceTab(activeTab)}
        </section>
      </main>
    </div>
  );
}
