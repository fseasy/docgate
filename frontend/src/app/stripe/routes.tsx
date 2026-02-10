import StripeContextLayout from "./StripeContextLayout";
import { ROUTES } from "../../routes";
import { SessionAuth } from "supertokens-auth-react/recipe/session";
import CheckoutPage from "./checkout";
import ReturnPage from "./return";
import { Route } from "react-router-dom";

export const getStripeRoutes = () => {
  return (
    // Use Layout for provider context. 
    <Route element={<StripeContextLayout />}>
      // !NOTE: within the SessionAuth wrapper
      <Route path={ROUTES.STRIPE_CHECKOUT} element={<SessionAuth><CheckoutPage /></SessionAuth>} />
      <Route path={ROUTES.STRIPE_RETURN} element={<SessionAuth><ReturnPage /></SessionAuth>} />
    </Route>
  );
};