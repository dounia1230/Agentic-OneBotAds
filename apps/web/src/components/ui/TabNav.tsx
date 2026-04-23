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
  isCollapsed?: boolean;
  onChange: (tabId: WorkspaceTabId) => void;
};

export function TabNav({ tabs, activeTab, isCollapsed = false, onChange }: TabNavProps) {
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
    <div
      className={`tab-row ${isCollapsed ? "is-collapsed" : ""}`}
      role="tablist"
      aria-label="Workspace tabs"
      aria-orientation="vertical"
    >
      {tabs.map((tab, index) => {
        const isActive = tab.id === activeTab;
        const shortcut = tab.label
          .split(" ")
          .map((word) => word[0])
          .join("")
          .slice(0, 2);

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
            <span className="tab-shortcut" aria-hidden="true">{shortcut}</span>
            <span className="tab-label">{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
}
