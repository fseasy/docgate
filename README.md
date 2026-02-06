# docgate
A doc presentation site with auth


- 生成邀请链接
- 注册


## 环境配置

有这么几个模块：

1. React 前端(SPA), 嵌入了 Supertokens SDK
2. Hugo pages: 纯静态页面
3. fastapi based api.
4. Nginx 路由配置

整体是基于 nginx 来完成全部串联的，简单的来说，配置如下：

- /app/ => React SPA
- /docs/xx => Auth(fastapi) + Hugo Pages
- /api/ => fastapi
- / => Hugo Pages

