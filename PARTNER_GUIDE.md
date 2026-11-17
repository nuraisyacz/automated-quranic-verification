# Guide for the translation verification part

The report PDF, the certificate and the report page are shared. You do **not** need to change
them. You only need to make `verify_translation_rows` return the agreed result shape.

## What is shared (do not edit unless you must)

| File | What it does |
|---|---|
| `utils/report_generator.py` | Builds the report PDF (works for translation and Quranic text) |
| `utils/certificate.py` | Reference number, certificate PDF, hash helpers |
| `utils/result_contract.py` | The result shape + a checker (`contract_problems`) |
| `models.py` -> `VerificationCertificate` | Table where certificates are stored |
| `routes/verification_routes.py` | `/verify/translation` already issues certificates (see the `CERTIFICATE` block) |
| `VerifyDocumentPlaceholderPage.jsx`, `CertificateCheck.jsx` | The page and the public certificate-check page |
| `assets/fonts/` | Font used by the report PDF |

## What you provide: `verify_translation_rows(rows, lookup)`

It must return this (full description in `utils/result_contract.py`):

```python
{
  "summary": {
      "total_uploaded_rows": 10, "exact_matches": 9, "partial_matches": 1,
      "mismatches": 0, "reference_not_found": 0,
      "accuracy_percentage": 90.0,
      "verification_status": "partially_accurate",   # accurate | partially_accurate | inaccurate
      # optional: "invalid_rows", "missing_ayahs"
  },
  "details": [
      {"surah_number": 112, "ayah_number": 1, "status": "accurate",
       "similarity_percentage": 100, "uploaded_text": "...", "reference_text": "...",
       "message": ""},          # message is optional
  ],
  # optional: "coverage": {"scope": "Surah 112 (4/4 ayahs)"}   -> shown as "Scope checked"
}
```

**The one rule that matters:** `verification_status` is `"accurate"` **only when every row is an
exact match.** A certificate is issued only for `"accurate"` (100% accurate). One partial or
wrong row means no certificate.

Row `status` values: `accurate`, `partially_accurate`, `inaccurate`, `reference_not_found`,
`invalid_row`.

## How to check your work

Run the app and verify a translation file. If your function returns the wrong shape, the Flask
terminal prints lines starting with `translation result contract:` that say exactly what is
missing. The request still works; the messages are warnings only.

Then test these three files:
1. Every row exactly right -> status Accurate, a certificate appears, **Download Certificate** works.
2. One row slightly different -> Partially Accurate, **no** certificate.
3. A row with no reference -> No Reference, **no** certificate.

## Setup (once, same as the Quranic part)

```
pip install reportlab "qrcode[pil]" playwright
playwright install chromium
```
Make sure `backend/assets/fonts/amiri-arabic-400-normal.woff2` exists. The table
`verification_certificates` is created by `db.create_all()` (or your migration) and is shared by
both types.

## Notes

- The translation certificate does not show "Ayahs missing" (it only shows that line for Quranic
  text). If you want the translation flow to detect missing ayahs, add `missing_ayahs` to the
  summary and `coverage.scope`, then tell the certificate owner to enable the line.
- `reference_source` on the certificate is set in the `CERTIFICATE` block of `/verify/translation`.
  Change the label there if your reference has a different name.
- The report PDF prints translations left-to-right. Arabic in a translation file would also work.

## Git: avoid conflicts

`verification_routes.py` and `VerifyDocumentPlaceholderPage.jsx` contain both flows. Pull
before you start. Keep your edits inside `verify_translation` and in `utils/verification.py`, so
changes to the Quranic text part do not collide with yours.