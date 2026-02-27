from pathlib import Path

from .data_types import EnvConfT, NginxLogConf


class NginxConfGen(object):
  INDENT_SPACE = 2
  NGINX_LOG_NAME = "json_docgate"

  def __init__(self, c: EnvConfT):
    self._c = c

  def gen(self, out_path: Path):
    log_content = _ACCESS_LOG_FMT.format(NGINX_LOG_NAME=self.NGINX_LOG_NAME)
    auth_cache_content = _AUTH_CACHE_ZONE
    upstream_content = self._gen_upstream()
    server_content = self._gen_server()
    content = "\n\n".join([log_content, auth_cache_content, upstream_content, server_content])
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

    if n.access_log:
      log_line = f"access_log {n.access_log.setting} {self.NGINX_LOG_NAME};"
      conf_lines.append(log_line)
      _create_log_dir_if_necessary(n.access_log)
    if n.error_log:
      log_line = f"error_log {n.error_log.setting};"
      conf_lines.append(log_line)
      _create_log_dir_if_necessary(n.error_log)

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
    hugo_public_doc_path_pattern = _path_set2location_re(self._c.deploy.hugo_public_doc_paths)
    with_auth_part = _HUGO_AUTH_PART_FMT.format(
      DOC_PREFIX=self._get_doc_prefix(), HUGO_STATIC_DIR=hugo_static_dir, PUBLIC_DOC_SET_RE=hugo_public_doc_path_pattern
    )
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


_ACCESS_LOG_FMT = r"""
log_format {NGINX_LOG_NAME} escape=json '{{'
    '"time":"$time_iso8601",'         
    '"remote_addr":"$remote_addr",'
    '"method":"$request_method",'      
    '"uri":"$request_uri",'            
    '"status":$status,'
    '"request_time":$request_time,'   
    '"upstream_rt":"$upstream_response_time",' 
    '"auth_rt":"$auth_request_time",' 
    '"auth_status":"$auth_status",' 
    '"upstream_addr":"$upstream_addr",'  
    '"upstream_status":"$upstream_status",'
    '"body_bytes":$body_bytes_sent,'
    '"host":"$host",'
    '"referer":"$http_referer",'
    '"ua":"$http_user_agent"'
'}}';
"""

_AUTH_CACHE_ZONE = r"""
proxy_cache_path /tmp/nginx_docgate_auth_cache # a general path for linux & mac
  levels=1:2
  keys_zone=docgate_auth_cache:1m # memory cache for key, 1MB memory key - enough for 1K+ users
  max_size=10m # disk cache for response, our auth only return code, so it's enough
  inactive=5m  # clean after 5min
  use_temp_path=off; # temporary files will be put directly in the cache directory instead of follow proxy_temp_path
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


    # --- AuthCache Start ----
    proxy_buffering on; # It must be on, so that the cache can work. Or it'll always be MISS

    proxy_cache docgate_auth_cache;
    # Cookie token + possible http token; $cookie_sAccessToken => nginx extract the value of sAccessToken from Cookie
    proxy_cache_key "$cookie_sAccessToken$http_authorization";

    # avoid Cache Stampede / Thundering Herd
    proxy_cache_lock on;
    proxy_cache_lock_timeout 5s; # if backend failed to response in 5s, 
    proxy_cache_lock_age 10s; # allow old cache to avoid all miss when expiring

    # cache success cache for 60s. You can increase it but currently it's not necessary as auth is fast
    proxy_cache_valid 200 60s;
    proxy_cache_valid 401 403 2s; # cache fail cache shorter

    # avoid possible header from backend that disable cache (api may use set those headers)
    proxy_ignore_headers Cache-Control Expires Set-Cookie;
    # --- AuthCache End ---
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
    root {HUGO_STATIC_DIR};
    # default strategy: go auth
    auth_request /_docgate/auth_check;
    auth_request_set $auth_request_time $upstream_response_time;
    auth_request_set $auth_status $upstream_status;
    # debug for auth-cache; uncomment following 2 lines to enable debug
    # add_header X-Auth-Cache-Status $upstream_cache_status always;
    # add_header X-Debug-Cookie $cookie_sAccessToken always;

    error_page 401 = @session_handle_redirect;
    error_page 403 = @purchase_redirect;
    # avoid cache for index.html (because customer will access by /docs/xxx/), so rule is on this level.
    add_header Cache-Control "no-store, no-cache, must-revalidate, private";
    add_header Pragma "no-cache";
    add_header Expires 0;
    
    # * Special public subset (only the specific page & direct resource will be open)
    location ~* ^/{DOC_PREFIX}/{PUBLIC_DOC_SET_RE} {{
        auth_request off;
        try_files $uri $uri/ =404;
        add_header Cache-Control "public, max-age=3600";
        add_header Pragma "public";
        add_header Expires 3600;
    }}

    # * Resource rule1: add cache for none html resources under /docs/ (with auth by inherent)
    location ~* ^/{DOC_PREFIX}/.*\.(m4a|mp3|wav|pdf|jpg|jpeg|png|gif)$ {{
        try_files $uri =404;
        add_header Cache-Control "private, max-age=604800";
    }}

    # * Resource rule2: add cache for none html resources under /docs/ (without auth)
    location ~* ^/{DOC_PREFIX}/.*\.(css|js|woff|woff2|ttf|eot|svg|otf)$ {{
        auth_request off;
        root {HUGO_STATIC_DIR};

        try_files $uri =404;
        add_header Cache-Control "public, max-age=604800";
        add_header Pragma "public";
        add_header Expires 604800;
    }}

    try_files $uri $uri/ /{DOC_PREFIX}/index.html;
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
  s = str(p).rstrip("/")
  return f"{s}/"


def _path_set2location_re(paths: set[str] | None) -> str:
  import re

  # make it first match the longest one, because we have an extra suffix matching logic
  long2short_paths = sorted(paths or [], key=lambda v: len(v), reverse=True)
  safe_paths = [re.escape(p) for p in long2short_paths]
  inner_group = "|".join(safe_paths)
  inner_group = inner_group.replace(r"\-", "-")  # avoid the unnecessary `\-` escape

  # allowed resources
  exts = "mp3|mp4|m4a|wav|pdf|css|js|jpe?g|png|gif|svg|woff2?|otf|ttf|pdf"
  # 1. pure `/docs/` without any inner-group & suffix
  # 2. / & /index with a sub-path html
  # 3. any specific resources or in sub dir of `audios/`,`images/`
  suffix = rf"(?:index\.html|/|/index\.html|/(?:audios/|images/)?[^/]+\.(?:{exts}))?$"
  if inner_group:
    pattern = rf"(?:{inner_group}){suffix}"
  else:
    # if empty, only open the root
    pattern = suffix

  return pattern


def _create_log_dir_if_necessary(log_conf: NginxLogConf):
  if log_conf.type != "file":
    return
  log_path = Path(log_conf.setting)
  if not log_path.exists():
    # make parent log dir, or nginx will failed to start
    log_path.parent.mkdir(parents=True, exist_ok=True)
