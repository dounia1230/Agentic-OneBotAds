import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";

import App from "./App";
afterEach(() => {
  cleanup();
});

test("renders the workspace shell with accessible tabs", () => {
  render(<App />);

  expect(screen.getByLabelText(/OneBotAds/i)).toBeTruthy();
  expect(screen.getByRole("tab", { name: /Campaign Analysis/i }).getAttribute("aria-selected")).toBe("true");
  expect(screen.getByRole("button", { name: /Select campaign CSV/i })).toBeTruthy();
});

test("switches tabs and shows the selected workflow", () => {
  render(<App />);

  fireEvent.click(screen.getByRole("tab", { name: /Knowledge Base Q&A/i }));

  expect(screen.getByRole("heading", { name: /Ask the local RAG workflow/i })).toBeTruthy();
  expect(screen.getByRole("button", { name: /^Ask$/i })).toBeTruthy();
});

test("collapses and expands the sidebar", () => {
  render(<App />);

  const collapseButton = screen.getByRole("button", { name: /Collapse sidebar/i });

  fireEvent.click(collapseButton);
  expect(screen.getByRole("button", { name: /Expand sidebar/i })).toBeTruthy();

  fireEvent.click(screen.getByRole("button", { name: /Expand sidebar/i }));
  expect(screen.getByRole("button", { name: /Collapse sidebar/i })).toBeTruthy();
});
