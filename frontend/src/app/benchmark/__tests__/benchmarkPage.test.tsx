import { describe, it, expect } from "vitest";
import React from "react";
import { render, screen } from "@testing-library/react";
import BenchmarkPage from "../page";

describe("BenchmarkPage Component", () => {
  it("renders the in-sample train split title without generalization claims", () => {
    render(<BenchmarkPage />);
    expect(
      screen.getByText("Train split, 14 scenarios, in-sample. Not a generalization.")
    ).toBeDefined();
  });

  it("renders the held-out un-run notice prominently", () => {
    render(<BenchmarkPage />);
    expect(
      screen.getByText(/Held-out evaluation has not been run\. Relevance labels have not been completed\./i)
    ).toBeDefined();
    expect(
      screen.getByText(/Held-out not run\./i)
    ).toBeDefined();
  });

  it("renders all critical caveats including deterministic decoding, placeholder digest, and event mismatch", () => {
    render(<BenchmarkPage />);
    expect(
      screen.getByText(/deterministic for fixed inputs and software/i)
    ).toBeDefined();
    expect(
      screen.getByText(/0x0000000000000000/i)
    ).toBeDefined();
    expect(
      screen.getByText(/Event-Definition Mismatch/i)
    ).toBeDefined();
  });

  it("renders the three dynamically computed Brier means", () => {
    render(<BenchmarkPage />);
    expect(screen.getByText("0.2511")).toBeDefined();
    expect(screen.getByText("0.2449")).toBeDefined();
    expect(screen.getByText("0.1611")).toBeDefined();
  });

  it("does not render any held-out scenario data in the results table", () => {
    const { container } = render(<BenchmarkPage />);
    const tableBody = container.querySelector("tbody");
    expect(tableBody).toBeDefined();
    expect(tableBody?.textContent).not.toContain("scen_15");
    expect(tableBody?.textContent).not.toContain("scen_16");
    expect(tableBody?.textContent).not.toContain("scen_20");
    // Ensure exactly 14 rows are rendered in the table
    const rows = tableBody?.querySelectorAll("tr");
    expect(rows?.length).toBe(14);
  });
});
