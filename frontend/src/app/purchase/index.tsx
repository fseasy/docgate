import { useState } from "react";
import ContentPageLayout from "../../component/ContentPageLayout";
import { SiteBanner } from "../../assets/images";
import { purchaseByCode } from "../../utils/api";
import { useNavigate } from "react-router-dom";
import { JumpOutSPARouteLogic, ROUTES } from "../../routes";

export default function Purchase() {
  const navigate = useNavigate();

  const [inviteCode, setInviteCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string; } | null>(null);

  const handleBindInviteCode = async () => {
    // 验证输入
    const trimmedCode = inviteCode.trim();
    if (!trimmedCode) {
      setMessage({ type: "error", text: "请输入预付款码" });
      return;
    }

    setIsLoading(true);
    setMessage(null);

    try {
      const result = await purchaseByCode(trimmedCode);

      if (result.fail_reason) {
        setMessage({ type: "error", text: `绑定失败：${result.fail_reason}` });
      } else {
        setMessage({ type: "success", text: "绑定成功！正在跳转到内容页..." });
        navigate(JumpOutSPARouteLogic.genRedirect2DocRoot());
      }
    } catch (error) {
      setMessage({
        type: "error",
        text: `绑定失败：${error instanceof Error ? error.message : "未知错误"}`
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ContentPageLayout>
      <Banner />

      {/* 方式 1：预付款码 */}
      <div className="mx-3 my-8">
        <h2 className="text-lg font-semibold  mb-3">方式 1：使用预付款码</h2>
        <p className="text-base-content/70 mb-4">
          如果你已经有预付款码，请在下面输入框填写即可验证并开启课程。
        </p>
        <div className="flex items-center mb-4 gap-2">
          <input
            type="text"
            placeholder="请输入预付款码"
            className="flex-6 input input-info p-3"
            value={inviteCode}
            onChange={(e) => setInviteCode(e.target.value)}
            disabled={isLoading}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !isLoading) {
                handleBindInviteCode();
              }
            }}
          />
          <button
            className="flex-1 btn btn-info"
            onClick={handleBindInviteCode}
            disabled={isLoading}
          >
            {isLoading ? (
              <span className="loading loading-dots loading-sm"></span>
            ) : (
              "验证"
            )}
          </button>
        </div>

        {/* 显示消息 */}
        {message && (
          <div role="alert"
            className={`alert ${message.type === "success" ? "alert-success" : "alert-error"} alert-soft mb-4`}>
            <span>{message.text}</span>
          </div>
        )}

        <p className="text-base-content/70 mb-2">如果你还没有预付款码，可以直接加大娟小红书或者微信（微信麻烦备注：亲子英语）。期待和你直接交流 <span className="text-base-content">😊</span> </p>

        {/* 二维码 */}
        <div className="flex justify-between gap-8 mt-6 sm:mx-10">
          <div className="flex flex-col items-center">
            <img src="/qrcode-xhs.png" alt="小红书二维码" className="w-32 h-32 mb-2" />
            <span className="text-base-content/70 text-sm">小红书</span>
          </div>
          <div className="flex flex-col items-center">
            <img src="/qrcode-wechat.png" alt="微信二维码" className="w-32 h-32 mb-2" />
            <span className="text-base-content/70 text-sm">微信</span>
          </div>
        </div>
      </div>

      {/* 分割线 */}
      <div className="divider">其他购买方式</div>

      {/* 方式 2：Stripe */}
      <div className="mx-3 my-8">
        <h2 className="text-lg font-semibold  mb-3">方式 2：直接支付</h2>
        <p className="text-base-content/70 mb-4">
          直接使用信用卡或 Stripe 支付，一键购买课程。
        </p>
        <button className="btn btn-info">
          使用 Stripe 支付
        </button>
      </div>
    </ContentPageLayout>
  );
}


export function Banner() {
  return (
    <>
      <div
        className='relative w-full aspect-1920/600 overflow-hidden sm:rounded-t-xl'
        style={{
          backgroundImage: `url(${SiteBanner})`,
          backgroundSize: "cover", // 使用 cover 确保铺满
          backgroundPosition: "center",
        }}
      >
        {/* 背景遮罩 */}
        <div className='absolute inset-0 bg-black/5' />

        {/* 3. 使用百分比定位文字，确保位置固定 */}
        <div className='absolute text-base-content/90 z-10 text-center top-[10%] right-[13%] sm:top-[25%] sm:right-[15%] '>
          {/* 4. 使用 vw 或 clamp 让文字大小也随屏幕缩放 */}
          <p className='text-lg sm:text-xl sm:tracking-widest sm:mb-1'>大娟的亲子英语</p>
          <p className='text-lg sm:text-xl sm:tracking-widest mb-1 sm:mb-6'> 让英语融入日常 </p>
          <p className='text-sm sm:text-xl sm:leading-relaxed text-gray-600 opacity-70 bg-orange-100 rounded-xl px-2 sm:px-4 py-1 inline-block'>
            现在就加入，让开口不再难
          </p>
        </div>
      </div >
    </>
  );
};
