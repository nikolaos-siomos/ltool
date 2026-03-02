# `ltool_scc` — SCC server CLI tool (`ltool.__ltool_scc__`)

## Overview

`ltool_scc` is the SCC-oriented CLI intended to run on a the SCC server. The module:

1. Parses command line arguments (`measurement_id`, `config_file`)
2. Reads the configuration file (`.ini`)
3. Queries SCC database for measurement input paths and product settings
4. Runs `get_layers(...)` for each configured product
5. Exports NetCDF output and updates SCC database

Entry point (from your `pyproject.toml`):

- `ltool_scc = "ltool.__ltool_scc__:main"`

---

## Command line arguments

- `-m`, `--measurement_id`  
  The measurement id that is going to be processed.

- `-c`, `--config_file`  
  Full path of the configuration file.

### Minimal example

```bash
ltool_scc   --measurement_id 20221019po04   --config_file /absolute/path/to/ltool.ini
```

---

## Configuration file (`ltool.ini`)

The configuration is read using Python `configparser`.

The template shipped with your package is located at:

- `src/ltool/templates/ltool.ini`

### Sections

#### `[database]`

Database connection parameters (strings). Typical fields:

- `host`
- `user`
- `password`
- `port`
- `socket`
- `scc-db-name`

#### `[scc]`

SCC processing and output parameters (strings). Typical fields:

- `input-dir`
- `output-dir` *(required for output writing)*
- `log-dir` *(optional; created if missing)*
- `log-level` *(used to set logging level)*

### Minimal example configuration

```ini
[database]
host=localhost
user=myuser
password=mypass
port=3306
socket=
scc-db-name=scc_database

[scc]
input-dir=/data/scc/input
output-dir=/data/scc/output
log-dir=/data/scc/logs
log-level=INFO
```
