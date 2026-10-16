# syntax=docker/dockerfile:1
FROM --platform=$BUILDPLATFORM golang:1.27.2-alpine@sha256:f92b6ef800e499660581efdabdf25d9d817a9d124eaf900924f0504e7e27e12d AS build
ARG TARGETARCH
ENV GOTOOLCHAIN=local GOMAXPROCS=2
WORKDIR /src
ADD --checksum=sha256:327391f301b79818f2418302516b4f6b41bdf08e38edc9011cc7f1b351e19452 https://codeload.github.com/smallstep/certificates/tar.gz/refs/tags/v0.30.2 /tmp/source.tar.gz
RUN echo '327391f301b79818f2418302516b4f6b41bdf08e38edc9011cc7f1b351e19452  /tmp/source.tar.gz' | sha256sum -c - && tar -xzf /tmp/source.tar.gz --strip-components=1 -C /src
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build go get golang.org/x/crypto@v0.58.0 golang.org/x/net@v0.61.0 && go mod tidy
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build go test ./authority/provisioner ./api ./logging
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build CGO_ENABLED=0 GOOS=linux GOARCH=$TARGETARCH go build -trimpath -ldflags='-s -w -X main.Version=0.30.2-personal.1' -o /out/step-ca ./cmd/step-ca && cp go.mod go.sum /out/
FROM smallstep/step-ca:0.30.2@sha256:a2b17872915c193259b75a5474c398326f41bd199f0842093e52cf4182bc8270
COPY --from=build /out/step-ca /usr/local/bin/step-ca
COPY --from=build /out/go.mod /out/go.sum /usr/local/share/step-ca-build/
