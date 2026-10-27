# Logical Components — u1-skeleton

Bridges the NFR designs (`performance-design.md`, `security-design.md`, `reliability-design.md`, `observability-design.md`) with the components in `inception/domain-design/components.md` and the functional design in `construction/u1-skeleton/functional-design/functional-spec.md`. The project is local, so there is no infrastructure beyond the machine.

| Logical component | Runs as | Failure domain | Where NFR patterns apply |
|-------------------|---------|----------------|--------------------------|
| Prepare command | One process (Spark local) | Its own run; leaves no manifest on failure | Read-only dump access; anonymisation; atomic writes; step summary |
| Train command | One process (Spark local) | Its own run | Input marker check; atomic writes; step summary |
| Index command | One process | Its own run | Atomic writes; manifest written last; step summary |
| Web app | One uvicorn process on 127.0.0.1 | Its own process; refuses to start on bad files | Startup checks; input validation; allow-listed responses; request logging; health |
| Built files folder (git-ignored) | Shared folder on disk | The disk | Written by commands, read-only to the app |

**Blast radius:** a failed command never damages the dumps or the last good manifest-backed files; a failing web app does not affect the commands. **Shared resource:** the built files folder is the only thing the processes share.
