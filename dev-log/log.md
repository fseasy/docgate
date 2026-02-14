## 26.02.14

### supertokens get_session 耗时约 0.8s

```
com.supertokens {"t": "2026-02-14T15:48:55.186862+00Z", "sdkVer": "0.30.2", "message": "getSession: using cookie transfer method", "file": "recipe/session/session_request_functions.py:150"}

com.supertokens {"t": "2026-02-14T15:48:55.186922+00Z", "sdkVer": "0.30.2", "message": "getSession: Value of antiCsrfToken is: False", "file": "recipe/session/session_request_functions.py:194"}

com.supertokens {"t": "2026-02-14T15:48:55.186956+00Z", "sdkVer": "0.30.2", "message": "getSession: Started", "file": "recipe/session/recipe_implementation.py:184"}

request get-session failed, elapsed= 0.008843916999467183
2026-02-14 23:48:55,195/DajuanEnglish/INFO/routes.py:271> AuthCheck: get exception of [No SuperTokens core available to query], redirect to session handle
      INFO   127.0.0.1:64829 - "GET /api/internal-auth/check HTTP/1.0" 401
com.supertokens {"t": "2026-02-14T15:48:55.198732+00Z", "sdkVer": "0.30.2", "message": "middleware: Started", "file": "supertokens.py:546"}
```

耗时这么长当然是因为网络问题，但问题是后面的验证不应该再走网络了呀？

没搞明白为啥还会走网络。

## 26.02.13

### css 选择器

再记录下，还是搞不清楚：

```
a.btn     /* <a class="btn">          标签a且有btn类 */
a .btn    /* <a> <x class="btn">      a里面的btn子元素； 注意这里和上面的区别，就是一个空格！所以不能乱写*/ 
a > .btn  /* <a> <x class="btn">      a里面的直接btn子元素 */
a, .btn   /* <a> 和 <x class="btn">   a标签或btn类 */
```

## 26.02.12

### 页面设计

原来可以把很多目录标签，作为 badge 来显示，看起来好漂亮。

## 26.02.11

### js 直接读取 access-token

### hugo config

https://gohugo.io/configuration/introduction/

1. For versions v0.109.0 and earlier, the site configuration file was named config. While you can still use this name, it’s recommended to switch to the newer naming convention, hugo.
   
   果然，最新的就是用 hugo.toml, 自己被坑着改回用 config.toml 了...

2. multiple configs

  To use a different configuration file when building your site, use the --config flag:

  hugo --config other.toml

  Combine two or more configuration files, with left-to-right precedence:

  hugo --config a.toml,b.yaml,c.json

  文件夹方式：

  ```
  my-project/
  └── config/
      ├── _default/
      │   ├── hugo.toml
      │   ├── menus.en.toml
      │   ├── menus.de.toml
      │   └── params.toml
      ├── production/
      │   ├── hugo.toml
      │   └── params.toml
      └── staging/
          ├── hugo.toml
          └── params.toml
  ```

  注意，每个文件名，对应的是一个 root-key （如 "params"）, 用这个 root-key 拆分为文件形式的子配置后，子配置里就不要写 root key 了！

3. 查看最终的 config: `hugo config` 展示实际应用的 config, 可以来 debug


## 26.02.10

### 接入 stripe 2

昨天发现 embeded ui 不能设置 dark/light 主题，决定改了；
但是被 Gemini 骗了—把后端改成了 pay intent 的方式；今天去看文档，发现还是有 create new session 的方式，只需要把 embeded ui 改成 custom 后端就完事了。

前端的变化，主要是要通过 Provider 注入 credit 和 appearance, 这个估计也可以不用 provider, 因为 Gemini 就不是这么写的，还是以前传参的方式。但不像被 Gemini 坑，就按文档的方式，只是让 kimi 给生成了一个仅作用在 strip 路由下的 provider — 通过 router-dom 的 Layout / <outlet> 来实现的。具体也不懂，反正折腾一上午，算是搞好了吧。

### 二维码定制化

需要把二维码放到网站上，但是导出微信、小红书导出的样式不统一、白底在 dark 下不好。尝试了 2 种：
1. 网上制作二维码—是挺绚丽的，结果发现，它把我的信息给改成了次级路由—也就是搞成了短链的形式，哎，而且这个短链还被微信封掉了…
2. 自己搞：把白色背景给去掉，换成透明的；结果—识别不了了… 算了，放弃了透明处理，就把大小统一下就行了吧…

### React lint 报错修复

每个错误都是在学习啊：

- Avoid calling setState() directly within an effect => 不要直接 setState, 会引起级联渲染。可以考虑用 Ref 不会触发渲染逻辑。或者想想，怎么需要 seState 吗？
- Cannot create components during render => 组件里不能再创建组件！移出去。


- 永远不要在 Hook 或 Component 的顶层作用域直接写 fetch 或 setState（除非是在初始化 state 的闭包里），必须包裹在 useEffect 或事件回调函数中。


- 同步计算找 useMemo/useState初始化，异步请求找 useEffect + setState。 现在清楚一点了吗？
  
同步逻辑：能不写在 Effect 里的就不写（第一种情况）

```ts
useEffect(() => {
  const tURL = 计算URL(); // 同步计算
  setTgtURL(tURL); // ❌ 这里不推荐
}, []);
```

 异步逻辑：必须写在 Effect 里

```ts
useEffect(() => {
  const fetchData = async () => {
    const data = await api(); // 异步等待
    setEmailStatus(data);      // ✅ 这里必须写 setState
  };
  fetchData();
}, []);
```

- 违反了 Hooks 规则 (Rules of Hooks)： React 不允许在 return 之后调用 Hook，也不允许在条件语句中调用 Hook。
  
  必须定义完了 Hook (useEffect 等)，才能开始 return.

  React 依靠 Hook 调用的顺序来记录状态。如果某次渲染执行了 return（即跳过了后面的 useEffect），而下次渲染又执行了它，React 的内部计数器就会错乱。




React 的核心运行机制：渲染周期（Render Cycle）

什么时候会再次执行这个函数？

- 在 React 中，一个自定义 Hook（比如 useEmail）本质上就是一个普通的函数，但它会在以下几种情况下重新从头到尾执行一遍：
- 内部的 State 改变了：只要你调用了 setApiEmail 或 setFetching，React 就会说：“这个 Hook 的数据变了，我要重新运行这个函数，看看它返回的最新结果是什么。”
- 依赖的 Context 改变了：因为你用了 useSessionContext()，只要 session 里面的数据（比如 loading 状态、accessToken）变了，这个函数就会重新执行。
- 使用这个 Hook 的组件重新渲染了：如果父组件变了，Hook 也会跟着跑一遍。

- setState 本身就是为了引起函数重跑。

- 不设统一对象的原因： 为了能利用“计算出来的结果”直接返回（派生状态），减少不必要的 setState 导致的多次重绘。

- React 的精髓： 函数就像一个加工厂。输入（Props, State, Context）一变，工厂就重新开工，输出（Return 值）新的产品。


对下面代码做过程解析：

```ts
export const useEmail = (): EmailStatus => {
  const session = useSessionContext();
  const [apiEmail, setApiEmail] = useState<string | undefined>(undefined);
  const [fetching, setFetching] = useState(false);

  // 1. 提取 Payload 里的 Email
  const payloadEmail = session.loading ? undefined : session.accessTokenPayload?.email;

  // 2. 只有在 Payload 没数据，且 Session 加载完时，才发起 API 请求
  useEffect(() => {
    if (session.loading || payloadEmail) return;

    let isMount = true;
    const loadEmail = async () => {
      setFetching(true);
      try {
        const userData = await fetchSessionSupertokensUserById();
        if (isMount) setApiEmail(userData?.emails[0]);
      } catch (err) {
        console.error("Fetch user data failed", err);
      } finally {
        if (isMount) setFetching(false);
      }
    };

    loadEmail();
    return () => { isMount = false; };
  }, [session.loading, payloadEmail]);

  // 3. 计算最终状态 (Derived State)
  // 如果 Session 还在加载 -> Loading
  if (session.loading) return { loading: true };
  
  // 如果 Payload 有数据 -> 直接返回，不走 State 逻辑，无闪烁
  if (payloadEmail) return { loading: false, email: payloadEmail };

  // 如果正在请求 API -> Loading
  if (fetching) return { loading: true };

  // 最后返回 API 的结果
  return { loading: false, email: apiEmail };
};
```

逻辑执行全过程（时间线模拟）
我们来看看我的代码是怎么跑的：
第一阶段：初始化（挂载）
  useEmail 执行。
  session.loading 为 true。
  函数碰到 if (session.loading) return { loading: true }。
  返回结果，函数结束。
第二阶段：Session 数据到达（Context 更新）
  session 变了，触发 useEmail 第二次执行。
  session.loading 变为 false。
  计算 payloadEmail。
  情况 A： 如果 payloadEmail 有值。
    函数碰到 if (payloadEmail) return ...。
    直接返回数据。结束。不需要任何 set... 动作，也不需要 useEffect 跑完。
  情况 B： 如果 payloadEmail 没值。
    继续向下运行。
    函数最后碰到 return { loading: false, email: apiEmail } (此时 apiEmail 还是 undefined)。
    渲染出结果。
    渲染完成后，React 执行 useEffect。
    useEffect 里面调用 setFetching(true)。
第三阶段：API 请求开始
  setFetching(true) 触发 useEmail 第三次执行。
  因为 fetching 是 true，函数碰到 if (fetching) return { loading: true }。
  返回加载状态。
第四阶段：API 数据返回
  loadEmail 异步函数执行完，调用 setApiEmail('new-email') 和 setFetching(false)。
  触发 useEmail 第四次（也是最后一次）执行。
  最后一行返回 { loading: false, email: 'new-email' }。


- setState 是“立刻”执行的吗？

  这是一个常见的误区：setState 不是立刻修改状态变量，而是发起一个“更新请求”。

- 批量更新：一个 useEffect 流程里执行了多个 setState, React 18 后会等待整个流程跑完，再统一决定下一次的渲染（函数再次执行）

- 特殊情况：如果你真的需要立刻重绘
- 
  虽然极少用到，但 React 确实提供了一个 API 叫 flushSync，它可以强制 React 立刻同步更新 DOM：
  
  ```JavaScript
  import { flushSync } from 'react-dom';

  flushSync(() => {
    setCount(1); // 立刻重绘
  });
  // 这一行执行时，DOM 已经更新了
  ```

1. 为什么 Props 变了要重新运行？
   
  React 的核心思想是：UI = f(data)。
  这里的 data 就包含了 Props、State 和 Context。
  如果 f（你的函数）不重新运行，它怎么知道根据新的 props 应该产出什么样的新界面呢？

2. 举个例子
假设你的 useEmail 现在需要根据一个 userId 来获取邮箱：

```TypeScript
//               这里是输入 (Props/Arguments)
export const useEmail = (userId: string): EmailStatus => {
  console.log("工厂开工了，当前的 userId 是:", userId);

  const [apiEmail, setApiEmail] = useState<string | undefined>(undefined);
  const session = useSessionContext();

  // 这里的逻辑每次 userId 变了都会重新计算
  const payloadEmail = session.accessTokenPayload?.email;

  useEffect(() => {
    // 当 userId 变化时，这里会被触发
    console.log("执行异步请求，针对用户:", userId);
    // ... fetch 逻辑 ...
  }, [userId]); // 依赖项里有 userId

  // 这里的返回结果每次都会重新生成
  return { loading: false, email: payloadEmail || apiEmail };
};
```

执行流程：
父组件传进来 userId = "1"。
useEmail 第一次运行，打印：工厂开工了... 1。
父组件因为某种原因，把 userId 改成了 "2"。
React 发现输入变了，第二次运行 useEmail，打印：工厂开工了... 2。
1. “重新运行” vs “重新挂载” (重要区别)
这里新手最容易搞混：
重新运行 (Re-render)： 函数从第一行跑到最后一行。但是！React 很聪明，它会记住你之前用 useState 保存的值。useState 不会因为函数重跑而重置为初始值（除非组件彻底从页面上消失了）。
重新计算： 函数内部那些普通的变量（比如你的 const payloadEmail = ...）确实会每次都重新计算。
1. 如果计算过程很重怎么办？
如果你担心：“既然 Props 一变函数就重跑，那我函数里有个循环 100 万次的计算逻辑，岂不是卡死了？”
这时候 React 给了你**“保险箱”**：
useMemo：

```ts
const expensiveValue = useMemo(() => {
   // 只有当 userId 变了，这里才会重新计算
   return performMillionIterrations(userId);
}, [userId]);
```

哪怕函数重跑了，只要 userId 没变，React 会直接从缓存里把上次的结果拿给你，跳过那 100 万次循环。

useEffect：

这也是为什么我们要把 fetch 放在 useEffect 里。如果函数每次重跑都去发请求，服务器就炸了。通过 [userId] 依赖数组，我们告诉 React：“虽然函数重跑了，但只要 userId 没变，就别再发请求了。”
总结：

Props 变了 -> 函数重跑（这是 React 的更新动力）。
State 变了 -> 函数重跑（这是组件的自我驱动）。
Context 变了 -> 函数重跑（这是全局环境的联动）。

你的 useEmail 逻辑：
正是利用了这种“重跑”机制。当 session 从 loading: true 变成 loading: false（Context 变了），useEmail 就会自动重跑。在重跑的过程中，它发现 session.loading 已经是 false 了，于是跳过了第一个 if，继续向下执行后面的逻辑。
这就是为什么我建议你用 “派生状态”：
既然函数反正要重跑，我们就在函数运行过程中，根据最新的 Props 和最新的 Context 实时计算出结果直接返回，这比手动管理一堆 setState 要清晰、高效得多。

## 26.02.09

### 接入 stripe

流程文档还是比较简洁的。

如何将 stripe 和自己逻辑嵌合？

1. 将一些数据放到 metadata, 或者绑定 `client_reference_id`
2. 在 webhook 中，处理数据库维度的更新 — 这里没有用户的 session.
3. 在跳转的 return 页面，处理 session 维度的更新（但是需要依赖数据维护的校验）—所以，这里对系统设计还是有点依赖的，必须得在数据库里存储一个权限相关的内容，用作 supertokens session 和 stripe 的桥梁。


## 26.02.08

### vibe coding

拿 copilot 直接生成了 logic bind code 的单测代码；

用 cline 直接生成了前端的代码—调用、设置…

### 耗时统计


**check** 接口

冷启动：

enter check, elapsed= 6.0829988797195256e-06
ready request get-session, elapsed= 7.333299799938686e-05
request get-session success, elapsed= 0.9524437500003842
request get-user-id success, elapsed= 0.9524577500014857
request get-user success, elapsed= 3.352637500000128

接着第二次：

enter check, elapsed= 1.2919990695081651e-06
ready request get-session, elapsed= 8.250000973930582e-06
request get-session success, elapsed= 0.0002462500015099067
request get-user-id success, elapsed= 0.00025262499912059866
request get-user success, elapsed= 1.9589982079996844

**get-supertokens-info** 接口

冷启动：

Enter get-supertokens-info: 0.00
get get-supertokens-info result: 1.67

第二次：

Enter get-supertokens-info: 0.00
get get-supertokens-info result: 0.83

总结：

- supertokens get user: 第一次 1.7s; 后续稳定 0.8s.
- get-session/verify-session: 无缓存情况下，大概是 1s；会缓存,第二次耗时基本忽略不计
- supabase: 稳定 2 s 左右…

### tailwind sm 表示超过小屏幕的情况

所以要写仅在小屏幕上应用的样式，应该直接写样式，再用 sm: 来覆盖这个样式。
如 `hidden sm:flex` 就是小屏幕 hidden, 超过小屏幕 flex.

###  React 里所有的组件在每次刷新都会被重新渲染

所以，组件顶层流里不能有副作用！特别是不能去刷新内容，因为这会套娃。

有副作用的，就放到 useEffect 里面，因为 useEffect 有监听触发对象限制，能够避免这个问题。


## 26.02.07

### Customize supertokens form submit button

现在登录、注册时间太长，默认的按钮样式就是增加 `...`. 看起来页面像卡住了，所以想把它变成 spinner 或者动态的 `...`.

搞了一下午，正常是走 override component. 但是文档看得不是很懂，搞了半天其实都没有覆盖到。
然后 ChatGPT 不太靠谱，方法不对。在我不断给相关代码后，还是给出了一些可行的方案，
然而我放进去就是不起效。

我就去问了 Gemini, 它的 override 方法也是错的。但是，它给了一个基于 css 的方案… 
是在 :disable 条件下做操作：
把原来的按钮文本给隐藏了，然后添加了一个 after 伪类，做了一个 ... 的 animates. 
我不认可这个方案，因为我认为它不是通过 :disable 添加的 ..., 而是通过内部的 isLoading 来添加的。
但是它说，在 isLoading = true 时，会设置 :disable 属性！
可以啊， 我试着贴进去看了下，哇塞，怎么这么丝滑…

服了 Gemini 了！

再看 override 的问题—吃饭的时候，我想肯定是自己作用域写错了，贴给 ChatGPT, 立刻就找到了问题。
然后 override 测试生效了，但没有再测试给我的替换 button 的方案了—既然 css 已经解决了，而且是对所有的 button 都生效的，还搞 override 干啥—这个 override 还得每个 form 对应去做呢。

总结下：

1. 先问 Gemini 吧，save life
2. 自己应该早点想到是作用域的问题，折腾半天，连 override 都没有入门，哎，确实能力不足。

### React Provider: 学习下 supertokens 是如何支持 override 的，之前为啥 override 没有生效

> from chatgpt

在 React（TS 只是类型系统，不改变 React 本身）里：

Provider 是 React Context API 的一种用法

它本质上就是一个组件，用来给它内部的子组件提供“共享数据/功能”

比如：

```tsx
<MyContext.Provider value={{ foo: 123 }}>
  <ChildComponent />
</MyContext.Provider>
```

ChildComponent 内部就可以通过 useContext(MyContext) 拿到 value

特点：

Provider 必须包住需要用到这个上下文的组件

子组件自动能拿到 Provider 提供的值

### SQLAlchemy 加锁写

使用 with_for_update.

一般不影响不用这个操作的请求。

## 26.02.06

### Datetime 迁移 supabase 处理

原来 impl = Datetime 建立的是无时区字段，但数据是有时区的，在 postgresql 里报错。

确实是自己写错了。应该写入都是无时区数据才对！

### React SPA 404 逻辑

1. 如果属于自己的资源（前缀满足），但走到了 404，说明无效路径，直接去 dashboard
2. 否则，可能属于其他资源，让 Nginx 来处理它—调用 window.location.href 赋值

### 概念学习

`{}` 与  `< />` 区别：前者是渲染变量；后者是渲染组件。

React 组件：返回 JSX 的函数或者类。

`return (<> </>)` 中 `<></>` 的意义：一个 JSX return 只能返回 1 个节点。
你也可以用`<div>` 来包裹多个节点，但是如果你不想包裹，就用`<></>`.

### alembic 迁移数据库

why：之前 prepaid-code 里有一个 bind_user_id 外链到 user 里的；现在我在做一个删除 user 的脚本；
删除后，其关联的 prepaid-code 的 bind_user_id 需要被设置为 null.

这个可以通过 foreignkey 的设置，让 db  自己来做。但是这需要改 schema. 

Sqlalchemy 下，就是用 alembic 这个工具（也是 sqlalchemy 下面的工具）；有一个 autogenerate 参数，
针对 foreignkey 的修改可以自动支持—太牛了！

迁移成功。不过我看它往 db 里写了一个 alembic_version 这个表… 好吧，本来也没啥。但是我这个是 dev 和 prod 共用的，不知道后续有没有问题。

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
