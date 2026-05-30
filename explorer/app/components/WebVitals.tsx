"use client";

import { useEffect } from "react";
import { onCLS, onFCP, onINP, onLCP, onTTFB } from "web-vitals";

type Metric = { name: string; value: number; rating: "good" | "needs-improvement" | "poor" };

function report({ name, value, rating }: Metric) {
  // CLS is unitless (0–1 scale), multiply by 1000 for integer storage.
  // All others are milliseconds — round to nearest int.
  const rounded = Math.round(name === "CLS" ? value * 1000 : value);
  window.umami?.track("web-vitals", {
    metric: name,
    value: String(rounded),
    rating,
  });
}

export default function WebVitals() {
  useEffect(() => {
    onCLS(report);
    onFCP(report);
    onINP(report);
    onLCP(report);
    onTTFB(report);
  }, []);
  return null;
}
