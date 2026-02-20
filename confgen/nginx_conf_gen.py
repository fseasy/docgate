from pathlib import Path

from .data_types import EnvConfT


class NginxConfGen(object):
  INDENT_SPACE = 2

  def __init__(self, c: EnvConfT):
    self._c = c

  def gen(self, out_path: Path):
    log_content = _DEBUG_LOG_FMT
    upstream_content = self._gen_upstream()
    server_content = self._gen_server()
    content = "\n\n".join([log_content, upstream_content, server_content])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, mode="wt", encoding="utf-8") as f:
      print(content, file=f)

  def _gen_upstream(self) -> str:
    d = self._c.deploy
    auth_upstream = _gen_block_conf(
      "upstream api_server",
      [
        "# max_fails=0: avoid block this server when it's down",
        f"server {d.backend_server} max_fails=0;",
        "keepalive 32;",
      ],
    )
    confs = [auth_upstream]

    if self._c.deploy.vite_in_server_mode:
      vite_upstream = _gen_block_conf("upstream vite_server", [f"server {d.vite_server};"])
      confs.append(vite_upstream)
    return "\n".join(confs)

  def _gen_server(self) -> str:
    main_server = self._gen_main_server_block()
    servers = [main_server]
    n = self._c.deploy.nginx
    if n.standard_reverse_proxy:
      assert n.server_name, "server-name must exist in standard reverse proxy mode"
      _80_server = self._gen_80_redirect_server(n.server_name)
      servers.append(_80_server)
    return "\n\n".join(servers)

  def _gen_main_server_block(self) -> str:
    n = self._c.deploy.nginx
    if not n.standard_reverse_proxy:
      conf_lines = [f"listen {n.listen_port};"]
    else:
      conf_lines = [
        "listen 443 ssl;",
        "listen [::]:443 ssl;",
      ]
      assert n.ssl_conf_lines, "SSL conf is empty in standard reverse proxy"
      conf_lines.extend(n.ssl_conf_lines)
    if n.server_name:
      server_line = f"server_name {n.server_name};"
      conf_lines.append(server_line)
    else:
      assert not n.standard_reverse_proxy, "server_name is required in standard reverse proxy"
    if n.access_log_path:
      log_line = f"access_log {n.access_log_path.absolute()} debug_log;"
      conf_lines.append(log_line)
      log_path = Path(n.access_log_path)
      if not log_path.exists():
        # make parent log dir, or nginx will failed to start
        log_path.parent.mkdir(parents=True, exist_ok=True)
    conf_lines.extend(
      [
        "",
        "client_max_body_size 1m;",
        "large_client_header_buffers 4 32k;",
        "# very important, to fix the error:",
        "# - `upstream sent too big header while reading response header from upstream`",
        "proxy_buffer_size          128k; ",
        "proxy_buffers              4 256k;",
        "proxy_busy_buffers_size    256k;",
        "",
      ]
    )
    # * auth-check
    conf_lines.append(_AUTH_CHECK)
    # * api
    api_line = _BACKEND_API_FMT.format(API_PREFIX=self._get_api_prefix())
    conf_lines.append(api_line)
    # * frontend start
    conf_lines.append(_FRONTEND_SEP)
    # * vite/react
    _vite_prefix = self._get_vite_prefix()
    if self._c.deploy.vite_in_server_mode:
      vite_inner_setting = _VITE_IN_SERVER_SETTING
    else:
      assert self._c.deploy.vite_static_dir, (
        f"Vite static dir {self._c.deploy.vite_static_dir} is invalid in static mode"
      )
      vite_inner_setting = _VITE_IN_STATIC_SETTING_FMT.format(
        VITE_STATIC_DIR=_ensure_path_endswith_slash(self._c.deploy.vite_static_dir), VITE_PREFIX=_vite_prefix
      )
    vite_section = _VITE_SECTION_FMT.format(VITE_SETTING=vite_inner_setting, VITE_PREFIX=_vite_prefix)
    conf_lines.append(vite_section)
    # * hugo/content
    hugo_static_dir = _ensure_path_endswith_slash(self._c.deploy.hugo_static_dir)
    normal_part = _HUGO_NORMAL_PART_FMT.format(HUGO_STATIC_DIR=hugo_static_dir)
    conf_lines.append(normal_part)
    with_auth_part = _HUGO_AUTH_PART_FMT.format(DOC_PREFIX=self._get_doc_prefix(), HUGO_STATIC_DIR=hugo_static_dir)
    conf_lines.append(with_auth_part)
    return _gen_block_conf("server", conf_lines)

  def _gen_80_redirect_server(self, server_name: str) -> str:
    conf_lines = [
      "listen 80;",
      "listen [::]:80;",
      f"server_name {server_name};",
      "return 301 https://$host$request_uri;",
    ]
    return _gen_block_conf("server", conf_lines)

  def _get_api_prefix(self) -> str:
    return self._c.basic.VITE_API_COMMON_BASE_PATH.strip("/")

  def _get_vite_prefix(self) -> str:
    return self._c.basic.VITE_WEBSITE_REACT_BASE_PATH.strip("/")

  def _get_doc_prefix(self) -> str:
    return self._c.basic.VITE_WEBSITE_DOC_ROOT_PATH.strip("/")


_DEBUG_LOG_FMT = r"""
log_format debug_log '$remote_addr - $remote_user [$time_local] '
'"$request" $status $body_bytes_sent '
'"$http_referer" "$http_user_agent" '
'uri=$uri args=$args '
'document_root="$document_root" '
'realpath="$realpath_root"';
"""

_AUTH_CHECK = r"""
# **************************
# ! backend/api part.
# **************************
# * for auth check from Nginx side (docgate kernel api)
location = /_docgate/auth_check {
    internal;
    proxy_pass http://api_server/api/internal-auth/check;

    proxy_set_header Host $host;
    proxy_pass_request_body off;
    proxy_set_header Content-Length "";
    proxy_set_header X-Original-URI $request_uri;
    proxy_set_header Cookie $http_cookie;

    proxy_http_version 1.1;
    proxy_set_header Connection "";

    proxy_connect_timeout 5s;
    proxy_send_timeout 60s;
    proxy_read_timeout 90s;

    proxy_intercept_errors off;  # return error code directly

    proxy_buffering off;
}
"""

_BACKEND_API_FMT = r"""
# * supertokens api proxy from Frontend side
location ^~ /{API_PREFIX}/ {{
    proxy_pass http://api_server;
    proxy_set_header Host $host;
    proxy_set_header Cookie $http_cookie;

    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    proxy_http_version 1.1;
    proxy_set_header Connection "";

    proxy_redirect off;
    proxy_connect_timeout 5s;
    proxy_read_timeout 90s;
    proxy_send_timeout 90s;

    proxy_intercept_errors off;  # return error code directly
    # Disable cache in browser side (avoid 301 issue when api failed temporarily)
    add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
}}
"""

_FRONTEND_SEP = r"""
# ******************************
# Frontend part.
# ******************************
"""

# Extra indent
_VITE_IN_SERVER_SETTING = r"""
  ## --------- proxy server version
  ##
  proxy_pass http://vite_server;

  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";

  proxy_set_header Host $host;
  proxy_set_header Cookie $http_cookie;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
  proxy_redirect off;
  proxy_connect_timeout 5s;
  proxy_read_timeout 300s;
  # Debug header: shows the actual file being served
  add_header X-Debug-Location "app-location";
  add_header X-Debug-File "$request_filename";
"""

# Keep the extra indent
_VITE_IN_STATIC_SETTING_FMT = r"""
  ## -------- Static version
  ## --------
  alias {VITE_STATIC_DIR};
  try_files $uri $uri/ /{VITE_PREFIX}/index.html; # all page routers are at index.html. $uri is for static resources.
"""

_VITE_SECTION_FMT = r"""
# ---- React part (they share the common /app/ prefix, to make the routing easier)
# - including 1. /st-auth/ 2. /manage 3. /purchase, ...
location ^~ /{VITE_PREFIX}/ {{
{VITE_SETTING}
}}
# ---- End of React Part
"""

_HUGO_NORMAL_PART_FMT = r"""
# ---- Hugo normal part
# * The lowest priority router, targeting Hugo site => website's index will locate at hugo part.
location / {{
    root {HUGO_STATIC_DIR};
    try_files $uri $uri/ /index.html;
}}
# ---- End of hugo normal part.
"""

_HUGO_AUTH_PART_FMT = r"""
# ---- Doc & Auth & redirect
# * `/docs/` is the VIP resource under auth protection.
# ! use `^~ (longest matching prefix)` for higher priority
# * `^~` means longest-prefix-matching, the higher order matching rule!
location ^~ /{DOC_PREFIX}/ {{
    auth_request /_docgate/auth_check;
    auth_request_set $auth_status $upstream_status;

    error_page 401 = @session_handle_redirect;
    error_page 403 = @purchase_redirect;

    root {HUGO_STATIC_DIR};
    try_files $uri $uri/ /{DOC_PREFIX}/index.html;

    # avoid cache for index.html (because customer will access by /docs/xxx/), so rule is on this level.
    add_header Cache-Control "no-store, no-cache, must-revalidate, private";
    add_header Pragma "no-cache";
    add_header Expires 0;
}}

# * add cache for none html resources under /docs/
location ~* ^/{DOC_PREFIX}/.*\.(m4a|mp3|wav|pdf|jpg|jpeg|png|gif|css|js|woff|woff2|ttf|eot|svg|otf)$ {{
    auth_request /_docgate/auth_check;

    root {HUGO_STATIC_DIR};

    try_files $uri =404;
    add_header Cache-Control "private, max-age=604800";
}}

# * 50x is from api, so return a json will be safer
error_page 500 502 503 504 /50x;
location = /50x {{
    internal;
    default_type application/json;
    return 502 '{{"code": 502, "message": "Backend server is down"}}';
}}

# * go to api interface for session refresh and redirect
location @session_handle_redirect {{
    return 302 /api/internal-auth/refresh-session-or-signin?s=$request_uri;
}}

location @purchase_redirect {{
    return 302 /app/purchase/;
}}
"""


def _gen_block_conf(block_head: str, content_lines: list[str], base_indent_level: int = 0) -> str:
  """
  Generate result as:
  {block-head} {
    ${single_line for single_line in line.split("\n") for line in content_lines}
  }
  """
  base_indent = " " * (base_indent_level * NginxConfGen.INDENT_SPACE)
  content_indent = base_indent + " " * NginxConfGen.INDENT_SPACE
  header_line = f"{base_indent}{block_head} {{"
  conf_lines = [header_line]
  for line in content_lines:
    for single_line in line.split("\n"):
      fmt_line = f"{content_indent}{single_line}".rstrip()  # truncate space of empty line
      conf_lines.append(fmt_line)
  close_line = f"{base_indent}}}"
  conf_lines.append(close_line)
  return "\n".join(conf_lines)


def _ensure_path_endswith_slash(p: str | Path) -> str:
  s = str(p)
  s.rstrip("/")
  return f"{s}/"
