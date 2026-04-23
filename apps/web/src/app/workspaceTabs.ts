export const workspaceTabs = [
  { id: "marketing-assistant", label: "Marketing Assistant" },
  { id: "campaign-analysis", label: "Campaign Analysis" },
  { id: "publication-generator", label: "Publication Generator" },
  { id: "knowledge-base-qa", label: "Knowledge Base Q&A" },
] as const;

export type WorkspaceTabId = (typeof workspaceTabs)[number]["id"];

export function getWorkspaceTabId(tabId: WorkspaceTabId): string {
  return `workspace-tab-${tabId}`;
}

export function getWorkspacePanelId(tabId: WorkspaceTabId): string {
  return `workspace-panel-${tabId}`;
}
