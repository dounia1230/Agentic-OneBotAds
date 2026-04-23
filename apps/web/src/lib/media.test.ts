import { expect, test } from "vitest";

import { canPreviewImage, resolveMediaUrl } from "./media";

test("allows previews for outputs URLs served by the API", () => {
  expect(canPreviewImage("/outputs/images/test.png")).toBe(true);
});

test("normalizes windows-style outputs paths for previewing", () => {
  expect(resolveMediaUrl("outputs\\images\\test.png")).toBe("/outputs/images/test.png");
});
