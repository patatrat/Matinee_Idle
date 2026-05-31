"use client";

import { useReportWebVitals } from "next/web-vitals";

const UMAMI_URL = "https://analytics.radomski.co.nz";
const WEBSITE_ID = "65225d81-5bcd-43f3-8f8c-f72ad5c48d50";

export default function WebVitals() {
  useReportWebVitals((metric) => {
    fetch(`${UMAMI_URL}/api/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: "event",
        payload: {
          website: WEBSITE_ID,
          url: window.location.pathname,
          title: document.title,
          hostname: window.location.hostname,
          language: navigator.language,
          screen: `${window.screen.width}x${window.screen.height}`,
          [metric.name.toLowerCase()]: metric.value,
        },
      }),
    }).catch(() => {});
  });
  return null;
}
