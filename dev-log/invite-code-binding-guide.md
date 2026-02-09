# 邀请码绑定功能实现指南

## 功能概述

邀请码绑定功能允许用户通过输入邀请码来激活课程访问权限。该功能包含后端 API 和前端界面两部分。

## 架构说明

### 后端实现

#### 1. API 端点
- **路径**: `/user/purchase-by-code`
- **方法**: POST
- **认证**: 需要 SuperTokens session
- **位置**: `docgate/routes.py`

#### 2. 请求格式
```python
class UserBindPrepaidCodeReq(BaseModel):
  prepaid_code: str  # 邀请码，自动去除首尾空格，最小长度为1
```

#### 3. 响应格式
```python
class UserBindPrepaidCodeResp(BaseModel):
  error: str | None  # None 表示成功，否则包含错误信息
```

#### 4. 核心逻辑 (`docgate/logics.py`)

`PrepaidCode.binding()` 方法执行以下步骤：

1. **验证邀请码**
   - 从数据库查询邀请码（使用 `for_update` 锁定行）
   - 检查邀请码是否存在
   - 检查邀请码是否可用（未使用且未过期）

2. **处理用户数据**
   - 查询用户是否存在于本地数据库
   - 如果用户不存在（脏数据情况）：
     - 从 SuperTokens 获取用户信息
     - 创建用户并绑定邀请码
     - 直接返回
   - 如果用户存在：继续下一步

3. **执行绑定**
   - 标记邀请码为已使用
   - 更新用户权限等级为 GOLD
   - 设置支付方式为 PREPAID_CODE
   - 记录支付日志
   - 更新用户最后活跃时间
   - 提交数据库事务

#### 5. 数据模型 (`docgate/models.py`)

**PrepaidCode 表**:
```python
- id: int (主键)
- code: str (邀请码，长度10，有索引)
- lifetime: datetime (过期时间，UTC时区)
- has_used: bool (是否已使用)
- bind_user_id: str (绑定的用户ID，外键)
```

**User 表**:
```python
- id: str (用户ID，主键)
- email: str (邮箱)
- tier: Tier (权限等级：FREE, GOLD等)
- tier_lifetime: datetime | None (权限有效期，None表示永久)
- pay_method: PayMethod (支付方式)
- pay_log: str (支付日志)
```

### 前端实现

#### 1. API 路由配置 (`frontend/src/routes.ts`)
```typescript
const API_ROUTES = {
  PURCHASE_BY_CODE: "/user/purchase-by-code",
  // ...
}
```

#### 2. API 函数 (`frontend/src/utils/api.ts`)
```typescript
export const bindPrepaidCode = async (inviteCode: string): Promise<BindPrepaidCodeResult>
```

功能：
- 发送 POST 请求到后端 API
- 包含 session credentials
- 处理错误并返回统一格式

#### 3. 购买页面组件 (`frontend/src/app/purchase/index.tsx`)

**状态管理**:
- `inviteCode`: 用户输入的邀请码
- `isLoading`: 加载状态
- `message`: 成功/错误消息

**用户交互**:
- 输入框：实时更新邀请码
- 验证按钮：触发绑定流程
- 支持回车键快捷提交
- 加载时禁用输入和按钮
- **动态加载效果**：使用 DaisyUI 的 `loading-dots` 组件显示动态点点点

**反馈机制**:
- 显示错误消息（红色警告框）
- 显示成功消息（绿色警告框）
- 成功后1.5秒自动跳转到首页

## 使用流程

### 管理员生成邀请码
1. 管理员登录系统
2. 访问管理页面
3. 点击"生成邀请码"按钮
4. 复制生成的邀请码并分享给用户

### 用户使用邀请码
1. 用户注册/登录系统
2. 访问购买页面 (`/purchase`)
3. 在"方式1：使用预付款码"区域输入邀请码
4. 点击"验证"按钮或按回车键
5. 等待验证结果（按钮显示动态加载点）：
   - 成功：显示成功消息，自动跳转到课程
   - 失败：显示错误原因，可重新输入

## 错误处理

### 常见错误场景

1. **邀请码不存在**
   - 错误信息：`prepaid-code [xxx] not found in db`
   - 原因：输入的邀请码未在系统中生成

2. **邀请码不可用**
   - 错误信息：`prepaid-code [xxx] can't been bind, reason=[...]`
   - 可能原因：
     - 邀请码已被使用
     - 邀请码已过期（超过14天）

3. **网络错误**
   - 错误信息：`Failed on api call, status=xxx`
   - 原因：网络连接问题或服务器错误

4. **会话过期**
   - 自动重定向到登录页面
   - 用户需要重新登录

## 数据库事务

绑定过程使用数据库事务确保数据一致性：
- 使用 `for_update=True` 锁定相关行
- 所有操作在同一事务中完成
- 任何错误都会回滚整个事务

## 安全考虑

1. **认证要求**: 所有 API 调用都需要有效的 SuperTokens session
2. **输入验证**: 
   - 后端：使用 Pydantic 验证，自动去除空格
   - 前端：检查空输入
3. **并发控制**: 使用数据库行锁防止竞态条件
4. **错误信息**: 不暴露敏感的系统内部信息

## UI/UX 特性

1. **动态加载指示器**: 使用 DaisyUI 的 `loading-dots` 组件
   ```tsx
   {isLoading ? (
     <span className="loading loading-dots loading-sm"></span>
   ) : (
     "验证"
   )}
   ```

2. **键盘快捷键**: 支持回车键提交
3. **状态反馈**: 清晰的成功/错误消息
4. **防重复提交**: 加载时禁用输入和按钮

## 测试建议

### 后端测试
```bash
# 使用 curl 测试 API
curl -X POST http://localhost:8000/user/purchase-by-code \
  -H "Content-Type: application/json" \
  -H "Cookie: your-session-cookie" \
  -d '{"prepaid_code": "test123456"}'
```

### 前端测试
1. 正常流程：输入有效邀请码
2. 错误处理：输入无效/已使用/过期的邀请码
3. 边界情况：空输入、特殊字符
4. 网络异常：断网情况下的表现
5. UI 测试：验证动态加载点的显示效果

## 相关文件

### 后端
- `docgate/routes.py` - API 端点定义
- `docgate/logics.py` - 业务逻辑实现
- `docgate/models.py` - 数据模型
- `docgate/repositories.py` - 数据库操作
- `docgate/exceptions.py` - 自定义异常

### 前端
- `frontend/src/app/purchase/index.tsx` - 购买页面
- `frontend/src/utils/api.ts` - API 调用函数
- `frontend/src/routes.ts` - 路由配置

## 未来改进

1. **邀请码批量生成**: 支持一次生成多个邀请码
2. **邀请码类型**: 支持不同类型的邀请码（试用、永久等）
3. **使用统计**: 记录邀请码的使用情况和来源
4. **邀请奖励**: 为邀请者提供奖励机制
5. **前端优化**: 添加邀请码格式提示和实时验证
6. **更丰富的加载动画**: 可以考虑使用 spinner 或其他动画效果