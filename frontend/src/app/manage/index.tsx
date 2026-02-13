import ContentPageLayout from "../../component/ContentPageLayout";
import { GenPrepaidCodeCard } from "./GenPrepaidCodeCard";
import { CreatePasswordResetLinkCard } from "./CreatePasswordResetLinkCard";
import { ManuallyVerifyEmailCard } from "./ManuallyVerifyEmailCard";

export default function ManageDashboard() {
  return (
    <ContentPageLayout>
      <div className='space-y-8'>
        <GenPrepaidCodeCard />
        <CreatePasswordResetLinkCard />
        <ManuallyVerifyEmailCard />
      </div>
    </ContentPageLayout>
  );
}
