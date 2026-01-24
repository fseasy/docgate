## 26.01.24

结论：
- 今天整体 demo 跑通。

TODO:
- 邮箱验证相关逻辑没做
- pay 页面和相关逻辑没做
- hugo 侧增加一个 dashboard 入口，方便退出、管理。
- Nginx config 自动生成——因为一些环境变量、react-frontend 使用方式（dev-server/build）需要在 nginx 侧配置

这些都先停下来，是时候去把 hugo 的页面给做出来，到时内容和这些功能都可以同步来做了。


### 继续 鉴权操作

继续做之前的方案：基于后端的 session refresh/redirect. 使用 Header 来传递 redirectToPath.

1. 在这里不能设置 header —— 因为它是给前端的参数！
2. qianwen 说的 `escaped_uri`, `escaped_request_uri` 全都是假的，根本不存在这个变量——ChatGPT 也不能识别；自己试了才知道，Gemini 倒是正确的。
3. 可以给 nginx 装一个 njs 模块（似乎比较容易，看起来是一个 so），然后就可以用了。感觉太重了
4. 得了，直接用前面说的方法： 直接拼接！按特定规则读取

OK —— 基于拼接的操作 works smoothly. 有点丑，hardcode, 但是配好了肯定稳。
Python 侧用的 yarl, 自动处理 query encode 问题，跑下来终于通了。


### 再次要解决在 Supertokens SPA 里重定向的问题

现在后端重新到登录后，带上了它需要的 redirectToPath 参数，然而在 redirect 时 SPA 调用的是 navigate, 不会改变浏览器的地址，
导致不走 nginx 路由。

根据 [supertokens post-auth](https://supertokens.com/docs/post-authentication/post-login-redirect)，可以重写
get-redirection-URL 函数，总是重定向到一个入口，然后由这个入口去做浏览器重定向——所以，要再次透传 redirectToPath 到这个入口，
让这个落地页去执行 js window.location.replace 操作。

传这么多次，地址得保证有效，又得一顿测试吧——毕竟各个规范不同啊。

还好——每次透传因为只有这 1 个 query，所以直接用 indexOf + slice, 所以肯定不会掉。

### TS 语法： 变量作为对象字面量的 key 时，要加中括号 `[]`

表示“动态计算属性名”。如 `{[var]: xxx}`; 不然 `var` 会被当做一个 string 啊! 而不是变量。哈哈，挺有意思。




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

### Nginx 侧如何妥善传递 redirectToPath

1. 作为 query 传 = 靠公共的解析 query string 有风险——因为 path 没有 encode，可能有 ?&= 等特殊字符；但可以 trick 的自己去处理 query path, 毕竟数据是自己传的——只是这太 trick 了
2. (Gemini) 直接拼接到 path, 然后用 fastapi 的 {rest_of_str: path} 来提取——同样有 query 的问题。trick
3. (qianwen) set header ==> 感觉这个最简单直接

### 新的方案选择

可以在前端增加一个 monkey patch, 来直接处理 401 请求：

```
<script>
(function() {
    const originalFetch = window.fetch;

    // 劫持全局 fetch
    window.fetch = async function(...args) {
        // 1. 尝试发送原始请求
        let response = await originalFetch(...args);

        // 2. 如果发现是 401 (Session 过期)
        if (response.status === 401) {
            console.log("Session expired, trying to refresh...");

            try {
                // 3. 调用刷新接口 (这是 SuperTokens 的标准刷新端点)
                // 注意：这里用 originalFetch 防止死循环
                const refreshResponse = await originalFetch("/app/auth/session/refresh", {
                    method: "POST"
                });

                if (refreshResponse.ok) {
                    console.log("Refresh successful, retrying original request...");
                    // 4. 刷新成功，重试原始请求
                    // 浏览器会自动带上新的 Cookie
                    response = await originalFetch(...args);
                } else {
                    // 5. 刷新失败（Refresh Token 也过期了），去登录页
                    console.log("Refresh failed, redirecting to login");
                    window.location.href = "/app/auth/?show=signin&redirect_to=" + encodeURIComponent(window.location.pathname);
                }
            } catch (error) {
                console.error("Auto refresh logic failed", error);
            }
        }

        return response;
    };
})();
</script>
```

或者可以直接引入 supertokens 依赖，重新 init 一下就行。

优势：体验更丝滑；服务端少了一个额外的跳转接口
劣势：hugo 侧引入了太多的东西；而且这些 config 要共享到 hugo 侧，麻烦

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
