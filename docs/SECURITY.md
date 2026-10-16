# Pinned SSH CA security rebuild

Upstream step-ca 0.30.2 remains the feature baseline. Its bundled Go
dependencies precede fixes for GO-2026-5018 (SSH key parser denial of service)
and GO-2026-5025 (HTML parser). Do not expose the unpatched image.

`build/step-ca/Dockerfile` verifies the upstream source SHA-256, pins the
Go 1.27.2 builder and runtime images, updates x/crypto to 0.58.0 and x/net
to 0.61.0, and tests provisioners, API and logging before building. It records
the resulting module files inside the image. No host Go installation changes.

Run `docker compose --profile ssh build step-ca` before starting the SSH
profile. The resulting local image is `personal-access-step-ca:0.30.2-personal.1`.
Review subsequent upstream advisories and rebuild before upgrading production.
The unmodified upstream image is used only for offline initial key generation.

References:
- https://pkg.go.dev/vuln/GO-2026-5018
- https://pkg.go.dev/vuln/GO-2026-5025
- https://github.com/smallstep/certificates/issues/2730
