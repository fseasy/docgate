import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ContentPageLayout from "../../component/ContentPageLayout";
import { isPathPrefixBelongsToSPA, JumpOutSPARouteLogic, ROUTES } from "../../routes";

export default function NotFoundPage() {
  const pathname = window.location.pathname;
  const [redirectInfo, setRedirectInfo] = useState<React.ReactNode>(
    <p>Redirecting to <code>dashboard</code></p>
  );
  const navigate = useNavigate();

  useEffect(() => {
    const isInSPA = isPathPrefixBelongsToSPA(pathname);
    if (isInSPA) {
      // navigate to dashboard directly
      setTimeout(() => { navigate(ROUTES.DASHBOARD); }, 1000);

    } else {

      const fullUrl = window.location.href;
      setRedirectInfo(
        <p>Redirecting to <code>{fullUrl}</code></p>
      );
      // go to that page by jump out of spa. => NOTE, we directly set it to the whole href.
      const jumpUrl = JumpOutSPARouteLogic.genRedirectRelativeURL(fullUrl);

      setTimeout(() => { navigate(jumpUrl); }, 1000);
    }
  }, []);

  return (
    <ContentPageLayout>
      <div className="flex items-center justify-center h-[70vh]">
        <div className="card bg-base-100 h-[50vh] items-center justify-center w-full">
          <h2 className="text-5xl m-9">
            404 Page Not Found
          </h2>
          <div>
            <p><code>{pathname}</code> isn't a known url.</p>
            {redirectInfo}
          </div>
        </div>
      </div>

    </ContentPageLayout>
  );
}