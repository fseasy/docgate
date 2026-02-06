## 开发环境记录

1. nginx 配置
   
  配置目录： /opt/homebrew/etc/nginx/
  子目录 `/servers` 包含了这个 docgate 的路由配置，是直接软连接到这个仓库地址的 nginx/dev.conf 的

  日志地址：
  
  access: /opt/homebrew/var/log/nginx/dajuan-debug-access.log

  error: /opt/homebrew/var/log/nginx/error.log

  cmd:
  
  ```bash
  nginx -t 
  brew services restart nginx
  ```