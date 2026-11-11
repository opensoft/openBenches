# Research

- Native Windows rather than WSL: preserve evidence when guest transport fails; CIM/Task Scheduler are the declared native runtime.
- Latch timed-out paths rather than repeated recovery: killing a client cannot prove a blocked guest exited.
- Read cgroups rather than routine stats API calls: distinguish cache from application memory without amplifying suspect polling.
- Keep metrics only: raw configs, arguments, environments and application logs can contain secrets. Full dumps are high-overhead and separately approved.
- Sources: Docker daemon logging and Desktop diagnose CLI; Microsoft WSL troubleshooting; Linux wait(2). A related public bug does not establish this host's initiating event.
