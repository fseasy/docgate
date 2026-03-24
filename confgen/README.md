# Config Gen

collection all the config here, and generate corresponding config for each module:

- fastapi (backend)
- vite (frontend, auth)
- nginx

Put configs to `./uni-conf/$env/conf.py`. 

## Example conf

Those configs all will be git-ignored for safety.

But for example, we make an example dir in `./uni-conf/example` so you can based on these build your own setting.

You can first create one new dir as following:

```bash
- example/conf.py
- dev/ [new]
```

then copy `example/conf.py` to `dev/conf.py`, then run `uv run 