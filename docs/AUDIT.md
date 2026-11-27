# PatchScope audit

This is a lightweight self-audit, not an independent security or industrial validation report.

## Checks and corrections

- Prevented the common mislabeling of a nearest-neighbor texture baseline as PatchCore or a neural network. The UI, README and study guide describe exactly the four handcrafted features and brute-force distance method.
- Separated synthetic normal train seeds, normal-validation seeds, and test seeds. Training-only scaler/reference bank and validation-only cutoff reduce direct leakage. The test is tiny, from the same generator, and was inspected during development.
- Added explicit warnings that the 95th percentile from 12 normal samples does not guarantee a 5% real false-alarm rate; image AUC is not localization performance; colors are normalized per image.
- Reject unreadable, empty, oversized and too-small images, restrict to PNG/JPEG, cap pixel dimensions before full decode, and limit input bytes read. The multipart parser may spool files before the endpoint reads them; this is not a hardened request-body limit.
- Corrected stale upload filename when a synthetic sample is chosen; display the actual selected input type and clear output on errors.
- Localhost binding plus Host/Origin checks and CSP are partial defenses; no authentication. Do not expose this demo publicly or upload sensitive data.
- Ten automated tests check synthetic reproducibility, feature shape, input errors, response format and local-origin handling. Desktop/mobile browser smoke tests exercise samples and invalid upload. Tests do not establish real-world defect performance.

## Remaining issues

Grayscale resizing, coarse non-overlapping patches, simplistic features, a common generator and tiny test set can produce misleading results. Uploads cannot train a user-supplied normal reference. No pixel-level evaluation, real camera, pretrained model, calibration, multi-user security or external validation is provided. Linux was tested; Windows was not. Exact package versions are not locked.
