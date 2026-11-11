# Helper CI efficiency

For #250 and release 1.7, omit only proven duplicate ordinary helper CI while
retaining fast checks and all five exact-candidate integration environments.
Keep the two-file helper allowlist and manual queue receipts unchanged.
Mixed/uncertain/ordinary/manual events retain full checks. No live canary,
ruleset bypass, app-access or release changes, or 1.6.2 tag.
