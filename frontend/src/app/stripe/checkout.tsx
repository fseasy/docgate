import { useCallback, useState, useEffect, useMemo } from "react";
import { loadStripe } from '@stripe/stripe-js';
import {
  EmbeddedCheckoutProvider,
  EmbeddedCheckout
} from '@stripe/react-stripe-js';

import { SiteConfig } from "../../config";
import { getApiURL } from "../../routes";
import ContentPageLayout from "../../component/ContentPageLayout";

// Make sure to call `loadStripe` outside of a component’s render to avoid
// recreating the `Stripe` object on every render.
// This is your test publishable API key.
const stripePromise = loadStripe(SiteConfig.stripePublishableApiKey);

export default function CheckoutPage() {
  return (
    <ContentPageLayout>
      <CheckoutForm />
    </ContentPageLayout>
  );
};

const CheckoutForm = () => {
  const fetchClientSecret = useCallback(() => {
    // Create a Checkout Session
    return fetch(getApiURL("STRIPE_CREATE_CHECKOUT_SESSION"), {
      method: "POST",
    })
      .then((res) => res.json())
      .then((data) => data.clientSecret);
  }, []);

  const options = { fetchClientSecret };
  return (
    <div id="checkout">
      <EmbeddedCheckoutProvider
        stripe={stripePromise}
        options={options}
      >
        <EmbeddedCheckout />
      </EmbeddedCheckoutProvider>
    </div>
  );
};
