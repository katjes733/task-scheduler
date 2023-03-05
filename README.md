# task-scheduler

A simple task scheduler implemented with Python that runs in a docker container on a schedule

## Build

1. Turn on `Experimental Features` -> `Access experimental features` in Docker Desktop.
2. First time run `docker buildx create --use`.
3. Build and push building for `x86` and `arm`: `docker buildx build --platform linux/amd64,linux/arm64 --push -t <registry>/task-scheduler:latest .` where `<registry>` is to be replaced with your desired destination registry.
