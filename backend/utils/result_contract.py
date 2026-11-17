"""utils/result_contract.py - the result shape that the report page, the PDF report and the
certificate all rely on. Use it to check your own verification function.

A verification function (e.g. verify_translation_rows) must return a dict:

    {
      "summary": {
          "total_uploaded_rows": int,
          "exact_matches": int,
          "partial_matches": int,
          "mismatches": int,
          "reference_not_found": int,
          "accuracy_percentage": float,           # 0-100
          "verification_status": "accurate" | "partially_accurate" | "inaccurate",
          # optional (default 0 if absent): "invalid_rows", "missing_ayahs"
      },
      "details": [                                 # one entry per uploaded row
          {
            "surah_number": int, "ayah_number": int,
            "status": "accurate" | "partially_accurate" | "inaccurate"
                      | "reference_not_found" | "invalid_row",
            "similarity_percentage": float,
            "uploaded_text": str, "reference_text": str,
            "message": str,                        # optional, shown under the row
          }
      ],
      # optional: "coverage": {"scope": "Surah 112 (4/4 ayahs)", "missing": [...], ...}
    }

IMPORTANT: verification_status == "accurate" means EVERY row is an exact match. The certificate
is issued only for "accurate" results.
"""

REQUIRED_SUMMARY = ("total_uploaded_rows", "exact_matches", "partial_matches", "mismatches",
                    "reference_not_found", "accuracy_percentage", "verification_status")
REQUIRED_DETAIL = ("surah_number", "ayah_number", "status", "similarity_percentage",
                   "uploaded_text", "reference_text")
VALID_ROW_STATUS = {"accurate", "partially_accurate", "inaccurate", "reference_not_found", "invalid_row"}
VALID_OVERALL = {"accurate", "partially_accurate", "inaccurate"}


def contract_problems(result):
    """Return a list of human-readable problems (empty list = the result is fine)."""
    problems = []
    if not isinstance(result, dict):
        return ["result is not a dict"]
    summary = result.get("summary")
    details = result.get("details")
    if not isinstance(summary, dict):
        return ["result['summary'] is missing or not a dict"]
    if not isinstance(details, list):
        problems.append("result['details'] is missing or not a list")
        details = []

    for key in REQUIRED_SUMMARY:
        if key not in summary:
            problems.append("summary is missing '%s'" % key)
    if summary.get("verification_status") not in VALID_OVERALL:
        problems.append("summary['verification_status'] must be one of %s, got %r"
                        % (sorted(VALID_OVERALL), summary.get("verification_status")))

    for i, row in enumerate(details[:50]):  # first 50 rows are enough to catch a wrong shape
        for key in REQUIRED_DETAIL:
            if key not in row:
                problems.append("details[%d] is missing '%s'" % (i, key))
        if row.get("status") not in VALID_ROW_STATUS:
            problems.append("details[%d]['status'] must be one of %s, got %r"
                            % (i, sorted(VALID_ROW_STATUS), row.get("status")))

    # The certificate rule: 'accurate' must really mean 100% exact.
    if summary.get("verification_status") == "accurate" and details:
        bad = [d for d in details if d.get("status") != "accurate"]
        if bad:
            problems.append("summary says 'accurate' but %d row(s) are not accurate" % len(bad))
    return problems