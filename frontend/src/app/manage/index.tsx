import TopNavbar from "../../component/nav/TopNav";
import { customizeAuthURL } from "../../supertokens/url";
import { useClipboard } from "../../utils/frontendHooks";
import { useGenInviteCode } from "./useGenInviteCode";

export default function ManageDashboard() {
  const { result: genCodeResult, generate: genCode } = useGenInviteCode();

  const makeInviteLink = (code: string) => customizeAuthURL({ show: "signup", queryParams: { ic: code } });

  const isIdleOrLoading =
    genCodeResult.status === "idle" ||
    genCodeResult.status === "loading";

  const inviteCodeResponse = isIdleOrLoading
    ? ""
    : JSON.stringify(genCodeResult, null, 2);

  const inviteCodeStr =
    genCodeResult.status === "success" ? genCodeResult.code : "";

  const inviteCodeLink =
    genCodeResult.status === "success"
      ? makeInviteLink(genCodeResult.code)
      : "";

  const { copied, copyToClipboard } = useClipboard();

  return (
    <>
      <div className='min-h-screen bg-base-200'>
        {/* 顶部导航 */}
        <TopNavbar />

        {/* 主内容区 */}
        <div className='max-w-3xl mx-auto p-6'>
          <div className='card bg-base-100 shadow-xl'>
            <div className='card-body space-y-4'>
              {/* 标题 */}
              <h2 className='card-title text-xl'>生成邀请链接（预付款注册链接）</h2>

              {/* 操作按钮 */}
              <div className='flex gap-5'>
                <button
                  className='btn btn-primary w-fit'
                  onClick={genCode}
                  disabled={genCodeResult.status === "loading"}
                >
                  {genCodeResult.status === "loading" ? "生成中…" : "生成新的邀请链接"}
                </button>
                <button
                  className='btn btn-secondary w-fit'
                  disabled={genCodeResult.status != "success"}
                  onClick={() => copyToClipboard(inviteCodeLink)}
                >
                  {copied ? "已复制 ✓" : "复制链接"}
                </button>
              </div>

              <div className='divider' />

              {/* 结果区 */}
              <div className='space-y-3'>
                <div>
                  <div className='text-sm text-gray-500'>邀请链接</div>
                  <div className='font-mono break-all'>{inviteCodeLink || "—"}</div>
                </div>

                <div>
                  <div className='text-sm text-gray-500'>邀请码</div>
                  <div className='font-mono'>{inviteCodeStr || "—"}</div>
                </div>

                <div>
                  <div className='text-sm text-gray-500'>请求 API 结果（debug）</div>
                  <pre className='bg-base-200 rounded p-2 text-sm overflow-x-auto'>{inviteCodeResponse || "—"}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
