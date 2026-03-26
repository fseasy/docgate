# Docgate

[English](./README.md) | [中文](./README.zh.md)

Docgate 是一个面向 [大娟的亲子英语](https://dajuan.fseasy.top) 这类产品的内容访问控制方案。它的目标是在静态博客内容（如 hugo）之上增加一层鉴权，实现登录、邮箱验证、会员购买（预付码兑换、 Stripe 付费）能力。

它采用一个比较直接的模型：Nginx 负责入口和路由，React + FastAPI 负责鉴权、购买流程，静态内容则继续静态化交付，与此不做强绑定（但针对需要开放权限的部分，还是需要通过 Config 在 Nginx 侧放开权限）。

## 产品

### 它解决什么问题

- 给静态文档或课程页面增加登录和权限控制。
- 同时支持预付码激活和 Stripe 自助购买。
- 让公开页面、应用页面和受保护文档保持解耦。
- 可以在小规格 Linux VPS 上直接部署，不依赖 Docker。

### 当前服务的产品

这个仓库当前支撑的是：

- `https://dajuan.fseasy.top`

如果你也有类似的产品，可以尝试使用该仓库。

### 主要用户流程

```text
预付码流程
管理员生成预付码 -> 用户登录 -> 用户兑换预付码 -> 后端将用户标记为已付费 -> 文档可访问

Stripe 流程
用户打开购买页 -> 创建 checkout session -> Stripe webhook 更新数据库 -> after-pay 同步角色 -> 文档可访问
```

## 技术

### 模块

- `confgen/`：统一配置生成器，用来生成 frontend env、backend env 和 Nginx 配置。
- `frontend/`：React SPA，负责认证 UI、用户面板、购买流程和管理工具。
- `backend/`：FastAPI 服务，负责用户状态、预付码、Stripe 以及内部鉴权接口。
- `deploy/`：面向 Linux 的非 Docker 部署脚本。

### 请求流转

```text
Browser
  |
  v
Nginx
  |-- /app/... ------------------> React SPA
  |-- /api/... ------------------> FastAPI backend
  |-- /docs/... -> auth_request -> FastAPI internal auth check
  |                                 |-- verify local JWT
  |                                 |-- check email verification
  |                                 `-- check paid role
  `-- / --------------------------> public static site
```

### 关键技术点

- 文档鉴权走本地 JWT 校验，而不是每次请求都调用 SuperTokens core。
- 通过 Nginx `auth_request` 做统一入口，受保护文档本身仍然可以保持静态。
- 利用 Nginx auth cache 减少重复鉴权请求。
- `confgen` 负责把 frontend、backend、Nginx 的配置统一起来。
- 整个方案针对低资源 VPS 做了取舍和优化。

### 模块文档

- [`frontend/README.md`](/Users/fseasy/workspace/dev-repo/docgate/frontend/README.md)
- [`backend/README.md`](/Users/fseasy/workspace/dev-repo/docgate/backend/README.md)
- [`confgen/README.md`](/Users/fseasy/workspace/dev-repo/docgate/confgen/README.md)
- [`deploy/README.md`](/Users/fseasy/workspace/dev-repo/docgate/deploy/README.md)

## 本地开发

日常开发的主入口是：

```bash
./run_dev_all.sh
```

这个脚本会启动：

- frontend dev server
- backend dev server

在这之前，你仍然需要先通过 `confgen` 生成环境文件；如果你想完整测试受保护文档流程，还需要本地可用的 Nginx 配置。

## 部署

在 Linux 上，推荐的部署方式很直接：先做一次机器初始化，之后用第二个脚本负责部署和更新。

```bash
cd deploy && \
./env_init.sh && \
./project_init_and_update.sh --mode deving/serving
```

更多细节见 [`deploy/README.md`](/Users/fseasy/workspace/dev-repo/docgate/deploy/README.md)。
