import { useState, useEffect, useRef } from "react";
import {
  useNavigate,
  Link
} from "react-router-dom";
import { JumpOutSPARouteLogic, getApiURL } from "../../routes";
import ContentPageLayout from "../../component/ContentPageLayout";
import { SiteConfig } from "../../config";
import { paywallAfterPayProcess } from "../../utils/api";

export default function ReturnPage() {
  return (
    <ContentPageLayout>
      <div className="flex items-center justify-center h-[70vh]">
        <div className="card bg-base-100 h-[50vh] items-center justify-center w-full">
          <ProcessContent />
        </div>
      </div>
    </ContentPageLayout>
  );
};

function ProcessContent() {
  const { processStep, customerEmail, errorContent } = usePayPostprocess();
  const navigate = useNavigate();

  useEffect(() => {
    if (processStep == "pay-cancel") {
      const timer = setTimeout(() => {
        navigate(JumpOutSPARouteLogic.genRedirect2IndexRoot());
      }, 3000);
      return () => clearTimeout(timer);
    } else if (processStep == "all-set") {
      const timer = setTimeout(() => {
        navigate(JumpOutSPARouteLogic.genRedirect2DocRoot());
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [processStep]);

  if (processStep == "query-pay-status") {
    return (
      <h2 className="text-2xl">
        查询支付状态中
        <span className="loading loading-dots loading-md"></span>
      </h2>
    );
  } else if (processStep == "pay-ok") {
    return (
      <>
        <h2 className="text-2xl">
          感谢！支付已成功！
        </h2>
        <h2 className="text-2xl">
          开始刷新登录状态并为 {customerEmail} 发送通知邮件。
          <span className="loading loading-dots loading-md"></span>
        </h2>
      </>

    );
  } else if (processStep == "pay-cancel") {
    return (
      <h2 className="text-2xl">
        支付已取消。3 秒后跳转到主页。
      </h2>
    );
  } else if (processStep == "all-set") {
    return (
      <h2 className="text-2xl">
        All set! 3 秒后跳转到文档主页。
      </h2>
    );
  } else if (processStep == "fail") {
    return (
      <>
        <h2>糟糕，出错了。如果你已经支付，请截图此页面并联系 {SiteConfig.contentAuthorName}.</h2>
        <h2>在 <Link to={JumpOutSPARouteLogic.genRedirect2DocRoot()}>主页</Link> 可找到联系方式。 </h2 >
        <div role="alert" className="alert alert-error">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 shrink-0 stroke-current" fill="none" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>{errorContent}</span>
        </div>
      </>
    );
  }

}

type ProcessStep = "query-pay-status" | "pay-ok" | "pay-cancel" | "all-set" | "fail";

const usePayPostprocess = () => {
  const [processStep, setProcessStep] = useState<ProcessStep>("query-pay-status");
  const [customerEmail, setCustomerEmail] = useState('');
  const [errorContent, setErrorContent] = useState('');

  const initialized = useRef(false); // Avoid React 18 strict mode that request twice in dev env

  useEffect(() => {
    if (initialized.current) return; // already run once
    initialized.current = true;

    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    const sessionId = urlParams.get('session_id');

    if (!sessionId) {
      setProcessStep("fail");
      setErrorContent("未知状态：无 pay session.");
      return;
    }

    const processRunFlow = async () => {

      try {
        const sessionApiURL = getApiURL("STRIPE_SESSION_STATUS");
        const res = await fetch(`${sessionApiURL}?session_id=${sessionId}`);
        if (!res.ok) {
          throw new Error(`Fetch Strip Session Status error! Status=${res.status}`);
        }
        const data = await res.json();
        setCustomerEmail(data.customer_email);

        if (data.status === 'complete') {
          setProcessStep("pay-ok");
          // NOTE: don't use `customerEmail`, it hadn't been synced here.
          const result = await paywallAfterPayProcess(data.customer_email);
          if (result.fail_reason) {
            setProcessStep("fail");
            setErrorContent(result.fail_reason);
          } else {
            setProcessStep("all-set");
          }
        } else if (data.status === 'open') {
          setProcessStep("pay-cancel");
        } else {
          setProcessStep("fail");
          setErrorContent(`Unknown pay status: ${data.status}`);
        }
      } catch (error) {
        console.log("After pay process failed", { error });
        setProcessStep("fail");
        setErrorContent(`${error}`);
      };
    };

    processRunFlow();

  }, []);

  return { processStep, customerEmail, errorContent };
};
