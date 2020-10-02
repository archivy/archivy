# Issues

This file lists all issues encountered in the building and testing of the Archivy image.

## For Version `0.2.0` and upwards

`pandoc` is a requirement for building images >= 0.2.0. But `pandoc` is not available for the following architectures:
- `arm/v6`
- `arm/v7`
- `arm64`
- `i386`
- `s390x`

Therefore, the Archivy image(version `0.2.0` and up) is being built for `amd64` architecture only.

Support for other architectures will be added as and when `pandoc` is available for those architectures.
