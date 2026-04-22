import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";

import App from "./App";

afterEach(() => {
  cleanup();
});

test("renders the workspace shell with accessible tabs", () => {
  render(<App />);

  expect(screen.getByRole("heading", { name: /Operator Studio/i })).toBeTruthy();
  expect(screen.getByRole("tab", { name: /Campaign Analysis/i }).getAttribute("aria-selected")).toBe("true");
  expect(screen.getByRole("button", { name: /Select campaign CSV/i })).toBeTruthy();
});

test("switches tabs and shows the selected workflow", () => {
  render(<App />);

  fireEvent.click(screen.getByRole("tab", { name: /Knowledge Base Q&A/i }));

  expect(screen.getByRole("heading", { name: /Ask the local RAG workflow/i })).toBeTruthy();
  expect(screen.getByRole("button", { name: /^Ask$/i })).toBeTruthy();
});
