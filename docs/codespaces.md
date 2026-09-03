# GitHub Codespaces guide

GitHub Codespaces is the recommended way to evaluate Dispatch. It provides an isolated cloud development environment and runs the complete Docker Compose stack without requiring a local installation.

## Start the platform

1. Open the repository on GitHub.
2. Select **Code**, then **Codespaces**.
3. Select **Create codespace on main**.
4. If GitHub asks whether you trust the repository, select **Yes, I trust the authors**.
5. Wait for the automatic setup to finish.

You can also use the direct link:

[Open Dispatch in GitHub Codespaces](https://codespaces.new/mikaelllll/Distributed-Job-Processing-System?quickstart=1)

The first creation takes longer because the development container and application images must be built. Later starts reuse cached layers when available.

## Automatic setup

The dev-container configuration automatically:

- provides Docker-in-Docker;
- creates an untracked `.env` file;
- generates random PostgreSQL, RabbitMQ, and Grafana credentials;
- builds the Compose images;
- starts the infrastructure and application services;
- scales the worker service to four instances;
- waits for the API and frontend health checks;
- forwards the application ports;
- prints direct service URLs.

No Python installation prompt needs to be accepted. Application dependencies run inside containers.

## Open the application

The Codespace does not open the website automatically. When startup finishes, the terminal prints a line like:

```text
Dispatch frontend: https://your-codespace-name-3000.app.github.dev
```

Open that address to use the application.

GitHub may wait for you to confirm **Yes, I trust the authors** before making the terminal available. If startup finishes while that prompt is waiting, its earlier terminal output may not be visible. This does not mean startup failed.

If the URL is not visible:

1. Open the VS Code **Ports** tab in the bottom panel.
2. Find **Dispatch frontend** on port **3000**.
3. Select the globe icon or right-click it and choose **Open in Browser**.

The public-looking forwarded URL is private to the Codespace unless you deliberately change its visibility.

| Port | Service |
| ---: | --- |
| 3000 | Dispatch frontend |
| 8000 | FastAPI and OpenAPI documentation |
| 15672 | RabbitMQ management |
| 3001 | Grafana |
| 9090 | Prometheus |

The frontend URL ends in `-3000.app.github.dev`. Opening port 8000 at its root displays API information rather than the React application. The service links are also printed again automatically whenever you reconnect to the Codespace.

## Useful lifecycle commands

The platform should start automatically. These commands are recovery and maintenance tools:

```bash
bash .devcontainer/print-urls.sh
bash .devcontainer/start-platform.sh
docker compose ps
docker compose logs -f
docker compose down
```

To remove all local service data as well:

```bash
docker compose down --volumes
```

## Troubleshooting

If port 3000 is missing, wait for the startup task to finish and inspect `docker compose ps`. The frontend, API, databases, broker, workers, generator, dispatcher, and aggregator should be running; health-enabled services should become healthy.

If a container failed, inspect it with:

```bash
docker compose logs SERVICE_NAME
```

If the Codespace was stopped rather than deleted, reopening it should restart the stack. If the environment is inconsistent, rebuild the development container from the VS Code command palette.

## Isolation and cost

Every visitor creates an independent Codespace with separate containers, volumes, credentials, and run history. They cannot access the repository owner's Codespace data.

Codespaces usage consumes the visitor's own GitHub quota. Stop or delete unused Codespaces from the GitHub Codespaces page to avoid unnecessary usage.
