import { useEffect } from "react";
import { genWebsiteFullURL } from "../../routes";
import { JumpOutSPARouteLogic } from "../../routes";
import ContentPageLayout from "../../component/contentPageLayout";

export default function JumpOutSPA() {
  const redirectURL = JumpOutSPARouteLogic.extractRedirectURLAndUnquote(window.location.href);
  const from = window.location.pathname;
  const rootURL = redirectURL || genWebsiteFullURL({ basePath: "/", queryParams: { from: from } });
  useEffect(() => {
    window.location.replace(rootURL);
  }, []);

  return (
    <ContentPageLayout>
      <div className="flex items-center justify-center h-[70vh]">
        <div className="card bg-base-100 h-[50vh] items-center justify-center w-full">
          <h2 className="text-3xl pad-6 mb-3">正在跳转...</h2>
          <a className="underline text-blue-200 hover:text-blue-500" href={rootURL}>点击手动跳转</a>
        </div>
      </div>
    </ContentPageLayout >
  );
}