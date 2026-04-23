import { useState } from "react";

import { TabNav } from "../components/ui/TabNav";
import { CampaignAnalysisTab } from "../features/campaign-analysis/components/CampaignAnalysisTab";
import { KnowledgeBaseTab } from "../features/knowledge-base/components/KnowledgeBaseTab";
import {
  MarketingAssistantTab,
  type SharedCampaignCsv,
} from "../features/marketing-assistant/components/MarketingAssistantTab";
import { PublicationGeneratorTab } from "../features/publication-generator/components/PublicationGeneratorTab";
import {
  getWorkspacePanelId,
  getWorkspaceTabId,
  workspaceTabs,
  type WorkspaceTabId,
} from "./workspaceTabs";

function renderWorkspaceTab(
  tabId: WorkspaceTabId,
  campaignCsv: SharedCampaignCsv | null,
  setCampaignCsv: (campaignCsv: SharedCampaignCsv | null) => void,
  setActiveTab: (tabId: WorkspaceTabId) => void,
) {
  switch (tabId) {
    case "marketing-assistant":
      return (
        <MarketingAssistantTab
          campaignCsv={campaignCsv}
          onCampaignCsvChange={setCampaignCsv}
        />
      );
    case "campaign-analysis":
      return (
        <CampaignAnalysisTab
          campaignCsv={campaignCsv}
          onOpenMarketingAssistant={() => setActiveTab("marketing-assistant")}
        />
      );
    case "publication-generator":
      return <PublicationGeneratorTab />;
    case "knowledge-base-qa":
      return <KnowledgeBaseTab />;
    default:
      return null;
  }
}

export default function App() {
  const [activeTab, setActiveTab] = useState<WorkspaceTabId>("marketing-assistant");
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [campaignCsv, setCampaignCsv] = useState<SharedCampaignCsv | null>(null);

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
        {workspaceTabs.map((tab) => {
          const isActive = tab.id === activeTab;

          return (
            <section
              key={tab.id}
              id={getWorkspacePanelId(tab.id)}
              className="workspace-panel tabpanel"
              role="tabpanel"
              aria-labelledby={getWorkspaceTabId(tab.id)}
              hidden={!isActive}
            >
              {renderWorkspaceTab(tab.id, campaignCsv, setCampaignCsv, setActiveTab)}
            </section>
          );
        })}
      </main>
    </div>
  );
}
