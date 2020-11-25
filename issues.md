# Issues

This file lists all issues encountered in the building and testing of the Archivy image.

## For version `0.2.0` and upwards

`pandoc` is a requirement for building images >= 0.2.0. But `pandoc` is not available for the following architectures:
- `arm/v6`
- `arm/v7`
- `arm64`
- `i386`
- `s390x`

Therefore, the Archivy image(version `0.2.0` and up) is being built for `amd64` architecture only.

Support for other architectures will be added as and when `pandoc` is available for those architectures.

## For version `0.0.7` and upwards

The ability to edit files on the host was added from version `0.0.7` onwards. Because of how this feature is implemented, it will not be available in the container images. Since Archivy tries to open the file for editing on the host, this will only work on an installation of Archivy that is not within a container.

Elasticsearch version >= `6.0` on `arm/v6` and `arm/v7` will not start unless `xpack.ml.enabled` is set to `false` in the `docker-compose-with-elasticsearch.yml` file. There are no such issues on other architectures.
