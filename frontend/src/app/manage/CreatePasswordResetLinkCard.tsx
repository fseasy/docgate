import { useState } from "react";
import { useCreatePasswordResetLink } from "./useCreatePasswordResetLink";

export function CreatePasswordResetLinkCard() {
  const { result, createLink } = useCreatePasswordResetLink();
  const [emailInput, setEmailInput] = useState("");

  const handleCreate = () => {
    if (emailInput.trim()) {
      createLink(emailInput.trim());
    }
  };

  return (
    <div className='card bg-base-100 shadow-xl'>
      <div className='card-body space-y-4'>
        <h2 className='card-title text-xl'>创建密码重置链接</h2>
        <p>
          正常情况用户可以直接在 UI 上点击 <em>忘记密码</em> 来获取重置链接。但正常流程下，这个链接是发送到他/她的邮箱的。
        </p>
        <p>
          如果用户邮箱是乱设置的，或者我们的 SMTP 服务有问题，就可以用这个来生成重置链接后发送给他/她。
          用户点击这个链接后，跳转到 UI 上就可以充值密码了。
        </p>

        <div className='flex gap-5 items-center'>
          <input
            type='email'
            placeholder='用户邮箱'
            className='input input-bordered w-full max-w-xs'
            value={emailInput}
            onChange={(e) => setEmailInput(e.target.value)}
          />
          <button
            className='btn btn-primary w-fit'
            onClick={handleCreate}
            disabled={result.status === "loading" || !emailInput.trim()}
          >
            {result.status === "loading" ? "处理中…" : "创建链接"}
          </button>
        </div>
        {result.status === "success" && (
          <div>
            <div className='text-sm text-gray-500'>密码重置链接</div>
            <div className='font-mono break-all'>{result.link}</div>
          </div>
        )}
        {result.status === "error" && (
          <div className='text-error'>错误: {result.error}</div>
        )}
      </div>
    </div>
  );
}
