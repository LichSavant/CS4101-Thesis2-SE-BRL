import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";
import { readArtifactDecision, type ArtifactDecision } from "@phishing-defense/shared";
import { ArtifactWorkbench, ArtifactResult } from "./ArtifactWorkbench";
import { submitArtifact } from "./api";

vi.mock("./api", () => ({ submitArtifact: vi.fn() }));
const submit = vi.mocked(submitArtifact);
function review(): ArtifactDecision {
  return { schema_version: "artifact-decision-1.0", run_id: "a".repeat(32), artifact_sha256: "b".repeat(64),
    modality: "content_bearing_email", status: "review_required", result_category: "not_evaluated", research_validated: false,
    classification: null, calibrated_probability: null, technical_findings: [], behavioral_evidence: [], attribution: null,
    decision: { tier: "review_required", reasons: ["compatible_bundle_unavailable"], severity: 0, coverage: .75, corroborating_families: [],
      policy_version: "test", policy_reference: "synthetic:test", policy_scope: "synthetic_fixture", actions: ["Verify independently."] },
    limitations: ["<script>alert('unsafe')</script>"], versions: { analysis: "test" }, timing_ms: { analysis_end_to_end: 1 } };
}
beforeEach(() => submit.mockReset());

it("requires explicit submission and body consent without assuming English", async () => {
  submit.mockResolvedValue(review());
  render(<ArtifactWorkbench/>);
  expect(screen.getByRole("button", { name: "Submit artifact" })).toBeDisabled();
  fireEvent.change(screen.getByLabelText("Artifact subject"), { target: { value: "Subject" } });
  fireEvent.change(screen.getByLabelText("Artifact content"), { target: { value: "Private body" } });
  fireEvent.click(screen.getByLabelText("I authorize analysis of these submitted fields"));
  fireEvent.click(screen.getByRole("button", { name: "Submit artifact" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("body authorization");
  expect(submit).not.toHaveBeenCalled();
  fireEvent.click(screen.getByLabelText("I authorize this body for the stated artifact analysis"));
  fireEvent.click(screen.getByRole("button", { name: "Submit artifact" }));
  await screen.findByRole("heading", { name: "REVIEW REQUIRED" });
  expect(submit.mock.calls[0][0]).toMatchObject({ language: "unknown", retain_metadata: false,
    artifact: { kind: "email", subject: "Subject", body: "Private body", body_collection_authorized: true } });
  expect(document.querySelector("script")).toBeNull();
});

it("clears an earlier result on input change and after an outage", async () => {
  submit.mockResolvedValueOnce(review()).mockRejectedValueOnce(new Error("Backend offline"));
  render(<ArtifactWorkbench/>);
  fireEvent.click(screen.getByLabelText("I authorize analysis of these submitted fields"));
  fireEvent.change(screen.getByLabelText("Artifact subject"), { target: { value: "First" } });
  fireEvent.click(screen.getByRole("button", { name: "Submit artifact" }));
  await screen.findByRole("heading", { name: "REVIEW REQUIRED" });
  fireEvent.change(screen.getByLabelText("Artifact subject"), { target: { value: "Second" } });
  expect(screen.queryByLabelText("Artifact decision")).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Submit artifact" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("Review Required: Backend offline");
  expect(screen.queryByLabelText("Artifact decision")).not.toBeInTheDocument();
});

it("exposes only email in the Phase 1 workbench", () => {
  render(<ArtifactWorkbench/>);
  const mode = screen.getByLabelText("Artifact mode") as HTMLSelectElement;
  expect(Array.from(mode.options).map(option => option.value)).toEqual(["email"]);
  expect(screen.queryByLabelText("Technical branch")).not.toBeInTheDocument();
});

it("rejects partial definitive and unsupported evidence envelopes", () => {
  expect(readArtifactDecision(review()).status).toBe("review_required");
  expect(() => readArtifactDecision({ ...review(), calibrated_probability: .01 })).toThrow("Incomplete");
  expect(() => readArtifactDecision({ ...review(), schema_version: "old" })).toThrow("Incompatible");
  expect(() => readArtifactDecision({ ...review(), behavioral_evidence: [{ state: "supported", evidence: [] }] })).toThrow("evidence");
  expect(() => readArtifactDecision({ ...review(), timing_ms: { invalid: Number.NaN } })).toThrow("Incompatible");
  const complete = { ...review(), status: "complete", result_category: "synthetic_model_generated", calibrated_probability: .5, classification: "legitimate",
    decision: { ...review().decision, tier: "informational" }, attribution: { channel: "model_attribution_not_artifact_evidence", method: "synthetic-test", space: "margin", selected_model_version: "synthetic-test", base_value: 0, explained_output: 1, omitted_contribution: 0, omitted_feature_count: 0, calibration_note: "synthetic", features: [{ feature: "test", value: 1, contribution: 1 }] } };
  expect(readArtifactDecision(complete).status).toBe("complete");
  expect(() => readArtifactDecision({ ...complete, attribution: { ...complete.attribution, explained_output: 2 } })).toThrow("attribution");
});

it("renders hostile strings as inert text and separates explanation channels", () => {
  render(<ArtifactResult result={review()}/>);
  expect(document.querySelector("script")).toBeNull();
  expect(screen.getByText("Deterministic behavioral evidence")).toBeInTheDocument();
  expect(screen.getByText("Model attribution — influence, not artifact evidence")).toBeInTheDocument();
  expect(screen.queryByText(/susceptibility/i)).not.toBeInTheDocument();
});
