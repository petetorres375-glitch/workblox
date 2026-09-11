// The one place the Business tool order lives. The nav bar and the Settings /
// signup tool picker both read from here, so the two lists can't drift apart
// the way they did when the picker fell back to whatever order /api/tools
// returned (which sorts by tool key, putting "Data Cleanup" ahead of
// "Business Email").
//
// Ordered by English display label rather than by key -- "email" renders as
// "Business Email" and so belongs in the B slot.
export const NAV_IDS = [
  "ad-copy", "batch-ats", "email", "contacts", "contract", "customer",
  "data-cleanup", "expenses", "hiring", "job-desc", "meeting", "policy",
  "proposal", "review", "social", "sop",
];

/** Sort whatever /api/tools returned into NAV_IDS order. Anything this build
 *  doesn't know about (a tool seeded on the backend before the frontend ships)
 *  keeps rendering, just at the end -- never dropped. */
export function inNavOrder(tools) {
  const rank = (key) => {
    const index = NAV_IDS.indexOf(key);
    return index === -1 ? NAV_IDS.length : index;
  };
  return [...tools].sort((a, b) => rank(a.key) - rank(b.key) || a.key.localeCompare(b.key));
}
