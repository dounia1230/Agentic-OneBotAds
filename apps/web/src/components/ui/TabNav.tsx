import { KeyboardEvent, useRef } from "react";

import {
  getWorkspacePanelId,
  getWorkspaceTabId,
  type WorkspaceTabId,
} from "../../app/workspaceTabs";

type TabNavProps = {
  tabs: ReadonlyArray<{
    id: WorkspaceTabId;
    label: string;
  }>;
  activeTab: WorkspaceTabId;
  onChange: (tabId: WorkspaceTabId) => void;
};

export function TabNav({ tabs, activeTab, onChange }: TabNavProps) {
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);

  function focusTabAt(index: number) {
    const tab = tabs[index];
    if (!tab) {
      return;
    }

    onChange(tab.id);
    tabRefs.current[index]?.focus();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    switch (event.key) {
      case "ArrowRight":
      case "ArrowDown":
        event.preventDefault();
        focusTabAt((index + 1) % tabs.length);
        break;
      case "ArrowLeft":
      case "ArrowUp":
        event.preventDefault();
        focusTabAt((index - 1 + tabs.length) % tabs.length);
        break;
      case "Home":
        event.preventDefault();
        focusTabAt(0);
        break;
      case "End":
        event.preventDefault();
        focusTabAt(tabs.length - 1);
        break;
      default:
        break;
    }
  }

  return (
    <div className="tab-row" role="tablist" aria-label="Workspace tabs">
      {tabs.map((tab, index) => {
        const isActive = tab.id === activeTab;

        return (
          <button
            key={tab.id}
            ref={(element) => {
              tabRefs.current[index] = element;
            }}
            id={getWorkspaceTabId(tab.id)}
            className={`tab-pill ${isActive ? "active" : ""}`}
            type="button"
            role="tab"
            aria-selected={isActive}
            aria-controls={getWorkspacePanelId(tab.id)}
            tabIndex={isActive ? 0 : -1}
            onClick={() => onChange(tab.id)}
            onKeyDown={(event) => handleKeyDown(event, index)}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
