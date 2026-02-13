import { useState } from "react";
import { useManuallyVerifyEmail } from "./useManuallyVerifyEmail";

export function ManuallyVerifyEmailCard() {
  const { result, verifyEmail } = useManuallyVerifyEmail();
  const [emailInput, setEmailInput] = useState("");

  const handleVerify = () => {
    if (emailInput.trim()) {
      verifyEmail(emailInput.trim());
    }
  };

  return (
    <div className='card bg-base-100 shadow-xl'>
      <div className='card-body space-y-4'>
        <h2 className='card-title text-xl'>手动验证用户邮箱</h2>
        <p>正常情况用户是通过点击发送到他/她邮箱里的链接来激活。</p>
        <p>
          但如果用户邮箱是乱设置的，或者我们的 SMTP 服务有问题，用户收不到邮件，可以用这个直接将他/她的账户激活，跳过邮箱验证阶段。
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
            onClick={handleVerify}
            disabled={result.status === "loading" || !emailInput.trim()}
          >
            {result.status === "loading" ? "处理中…" : "验证邮箱"}
          </button>
        </div>
        {result.status === "success" && (
          <div className='text-success'>邮箱验证成功</div>
        )}
        {result.status === "error" && (
          <div className='text-error'>错误: {result.error}</div>
        )}
      </div>
    </div>
  );
}
