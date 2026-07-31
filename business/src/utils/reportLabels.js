// Tool titles are authored for <Trans>, so they carry <0>…</0> markers around
// the highlighted word (e.g. "Contract <0>Analyzer</0>"). Exported reports are
// plain text, so the markers have to come off before the title is used as a
// heading in a .txt, .md or PDF report.
export function reportTitle(t) {
  return (t("title") || "").replace(/<\/?\d+>/g, "").replace(/\s+/g, " ").trim();
}
