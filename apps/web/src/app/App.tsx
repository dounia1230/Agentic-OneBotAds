import { useState } from "react";

import { PageHero } from "../components/ui/PageHero";
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

  return (
    <div className="shell app-shell">
      <PageHero
        eyebrow="Agentic OneBotAds"
        title="Operator Studio"
        description="A focused workspace for campaign review, publication packaging, grounded Q&A, and prompt-first visual ideation."
      />

      <TabNav tabs={workspaceTabs} activeTab={activeTab} onChange={setActiveTab} />

      <main className="workspace workspace-single">
        <section
          id={getWorkspacePanelId(activeTab)}
          className="panel composer tabpanel"
          role="tabpanel"
          aria-labelledby={getWorkspaceTabId(activeTab)}
        >
          {renderWorkspaceTab(activeTab)}
        </section>
      </main>
    </div>
  );
}
