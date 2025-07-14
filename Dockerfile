# syntax=docker/dockerfile:1.6   # enables BuildKit cache mounts

FROM astral/uv:python3.13-bookworm-slim


RUN useradd -m runner
USER runner
WORKDIR /home/runner/app
COPY --chown=runner:runner . .
RUN uv sync

EXPOSE 8000
CMD ["bash", "./entry.bash"]
