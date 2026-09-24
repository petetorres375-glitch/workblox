Sample Apple Pages documents for `tests/test_pages_reader.py`.

Copied from Apache Tika's test corpus (Apache License 2.0):
https://github.com/apache/tika/tree/main/tika-parsers/tika-parsers-standard/tika-parsers-standard-modules/tika-parser-apple-module/src/test/resources/test-documents

| File | Tika name | Format |
|---|---|---|
| `modern.pages` | `testPages2013.pages` | Pages 5 (IWA) — body text, a text box, a 4×3 table in the legacy cell layout |
| `legacy.pages` | `testPages.pages` | Pages '09 — `index.xml` + `QuickLook/Preview.pdf` |
| `legacy_password.pages` | `testPagesPwdProtected.pages` | Pages '09, password-protected |

No sample of a Pages file last saved by current Pages (2019+) exists here; the
current table cell layout is exercised instead with a table written by
numbers-parser, which uses the same archive format.
