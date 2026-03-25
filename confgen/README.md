# Config Gen

Collection all the config here, and generate corresponding config for each module:

- fastapi (backend)
- vite (frontend, auth)
- nginx

Put unified configs under `./src/docgate_confgen/unified_conf/$env/conf.py`.

## Example conf

Those configs all will be git-ignored for safety.

But for example, we make an example dir in `./src/docgate_confgen/unified_conf/example` so you can based on these build your own setting.

You can first create one new dir as following:

```bash
src/docgate_confgen/unified_conf/
├── example/conf.py
└── dev/conf.py
```

Then copy `src/docgate_confgen/unified_conf/example/conf.py` to `src/docgate_confgen/unified_conf/dev/conf.py`, and adjust the values for your own environment.

If needed, you can also create:

```bash
src/docgate_confgen/unified_conf/staging/conf.py
src/docgate_confgen/unified_conf/prod/conf.py
```

## Usage

Install dependencies first:

```bash
cd confgen
uv sync --no-dev --frozen
```

Prepare your env config:

```bash
mkdir -p src/docgate_confgen/unified_conf/dev
cp src/docgate_confgen/unified_conf/example/conf.py src/docgate_confgen/unified_conf/dev/conf.py
```

Run generator:

```bash
uv run python cli.py --env dev
```

You can also generate other env configs:

```bash
uv run python cli.py --env staging
uv run python cli.py --env prod
```

It will generate corresponding files for backend, vite and nginx based on the paths declared in `module_dir` attribute of the Config.
