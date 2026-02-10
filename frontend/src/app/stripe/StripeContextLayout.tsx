import { useMemo } from 'react';
import { Outlet } from 'react-router-dom';
import { loadStripe, type Appearance } from '@stripe/stripe-js';
import {
  CheckoutProvider
} from '@stripe/react-stripe-js/checkout';

import { SiteConfig } from "../../config";
import { getApiURL } from "../../routes";

const stripePromise = loadStripe(SiteConfig.stripePublishableApiKey);


export default function StripeContextLayout() {
  const clientSecretPromise = useMemo(() => {
    return fetch(getApiURL("STRIPE_CREATE_CHECKOUT_SESSION"), {
      method: 'POST',
    })
      .then((res) => res.json())
      .then((data) => data.clientSecret)
      .catch((error) => {
        console.log("Get error", { error });
      });;
  }, []);

  const isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const appearance: Appearance = {
    theme: isDarkMode ? 'night' : 'stripe',
  };

  return (
    <CheckoutProvider
      stripe={stripePromise}
      options={{
        clientSecret: clientSecretPromise,
        elementsOptions: { appearance },
      }}
    >
      {/* 核心：用 Outlet 渲染子路由，不再需要 <Routes> */}
      <Outlet />
    </CheckoutProvider>
  );
};