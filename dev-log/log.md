## 26.01.23

今天再次 review 了下 session 刷新的问题，本质还是 supertokens 和 hugo 部分完全脱节了——如果 hugo 嵌入了 supertokens api, 
其实就更好解决了——只需要后端返回 401, 它就自动刷新 session 了。但，这又是要重头再来的节奏——因为就是要把修改 hugo 的部分，把
supertokens 的前端逻辑写到 hugo 的 head 里——而且只能用裸 js 的方式——老实说，也没那么差，会让系统耦合更加紧密，免得出现现在这种问题。
但，这个又要重来一遍，而且如果完全不用 supertokens 前端，还得自己搞 auth 的前端。折腾啊。

### 新发现的问题： nginx 的 auth_request 只支持 401, 403, 2xx, 不支持其他 code

[doc](https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-subrequest-authentication/#response-codes)

我之前 407 来重定向到刷新 token，401 重定向到登录，403 重定向到购买。

现在登录问题统一返回 401 到一个后端，这个后端再去区分类型——所谓漏斗。

PS: gemini 3 pro preview 比免费的 ChatGPT 版本强太多了，ChatGPT 已经是各种乱说话了。


## 26.01.22

1. supertokens 提供的同步函数，原来是基于异步的 loop.run_in_executor 的封装——导致在异步调用里，调这个同步函数，就挂了…… 换成异步吧
2. 然后发现之前数据库操作都是写的同步，；但是 fastapi 接口都是异步，肯定异步最好啊——一狠心，全都重构了; sqlalchemy 异步接口倒是也稳定，而且比较简单；代码量倒是不太大；但是发现
3. 发现 nginx 做的 auth-check 有问题——不好处理 session token 刷新的问题。auth-request 只能处理 code，不能把 response header 传给前端，所以这个时候不能让通过返回 header 来刷新 session.
和各个 LLM 聊了半天，大概有 2 个方案： 

  1. 不用 nginx 做的复杂 routing 了，直接用 fastapi 代理全部。这样后端直接面向前端，刷新 session 更容易了——但是还是要自己处理 session 过期刷新的问题，因为发起请求的前端页面，没有 supertokens sdk, 不能在前端自动处理 401 自动刷新的逻辑；
     劣势：fastapi 抗静态文件，可能有瓶颈（小 QPS 还好，但是担心遇到大数据的时候，容易出问题）
     额外优势： nginx 配置会非常简单

  2. 还是现有的策略——额外处理下 refresh 的 code，让前端跳转到一个额外的接口，来做刷新写 cookie 的逻辑，同时再跳回来；
     劣势：nginx 配置复杂了
