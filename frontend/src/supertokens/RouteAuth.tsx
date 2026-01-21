import type { PropsWithChildren } from "react";
import { SessionAuth } from "supertokens-auth-react/recipe/session";
import { AccessDeniedScreen } from "supertokens-auth-react/recipe/session/prebuiltui";
import { UserRoleClaim /*PermissionClaim*/ } from "supertokens-auth-react/recipe/userroles";

const AdminRouteAuth = ({ children }: PropsWithChildren) => {
  return (
    <SessionAuth
      accessDeniedScreen={AccessDeniedScreen}
      overrideGlobalClaimValidators={(globalValidators) => [
        ...globalValidators,
        UserRoleClaim.validators.includes("admin"),
      ]}
    >
      {children}
    </SessionAuth>
  );
};

export default AdminRouteAuth;
