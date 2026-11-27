# Permission scope notes

- fs.read: read files under the project directory.
- fs.write: create or change files under the project directory.
- net.outbound: open connections to hosts outside the workstation.
- shell.exec: start processes through the system shell.
- env.read: read environment variables and dotenv files.

A tool that lists several scopes is judged by the most sensitive one. Read-only tools still need review when they
declare net.outbound, because the data they read can leave the machine.
