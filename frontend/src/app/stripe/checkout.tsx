import { useState } from "react";

import { PaymentElement, useCheckout } from '@stripe/react-stripe-js/checkout';


import ContentPageLayout from "../../component/ContentPageLayout";

export default function CheckoutPage() {

  return (
    <ContentPageLayout>
      <CheckoutForm />
    </ContentPageLayout>
  );
};


const CheckoutForm = () => {
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const checkoutState = useCheckout();

  if (checkoutState.type === 'loading') {
    return (
      <div className="card bg-base-100 shadow-xl rounded-none sm:rounded-xl h-48 flex flex-col items-center justify-center gap-3">
        <span className="loading loading-dots loading-lg text-primary"></span>
        <span className="text-sm font-medium text-base-content/70">Loading...</span>
      </div>
    );
  }

  if (checkoutState.type === 'error') {
    return (
      <div className="card bg-base-100 shadow-xl rounded-none sm:rounded-xl h-48 flex flex-col items-center justify-center gap-3">
        <div className="alert alert-error">Error: {checkoutState.error.message}</div>
      </div>
    );
  }
  const { checkout } = checkoutState;

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);
    const confirmResult = await checkout.confirm();
    // This point will only be reached if there is an immediate error when
    // confirming the payment. Otherwise, your customer will be redirected to
    // your `return_url`. For some payment methods like iDEAL, your customer will
    // be redirected to an intermediate site first to authorize the payment, then
    // redirected to the `return_url`.
    if (confirmResult.type === 'error') {
      setMessage(confirmResult.error.message);
    }

    setIsSubmitting(false);
  };

  return (
    <div className="max-w-md mx-auto w-full">
      <div className="card bg-base-100 shadow-xl rounded-none sm:rounded-xl">
        <form onSubmit={handleSubmit} className="card-body p-6">
          {/* 标题 */}
          <h3 className="card-title text-lg font-bold border-b pb-4 mb-4">订单信息</h3>

          {/* 商品列表 */}
          <ul className="space-y-3 mb-4">
            {checkoutState.checkout.lineItems?.map((item, index) => (
              <li
                key={index}
                className="flex justify-between items-center py-2 border-b last:border-b-0"
              >
                <span className="font-medium">{item.name} × {item.quantity}</span>
                <span className="font-semibold tabular-nums">{item.subtotal.amount}</span>
              </li>
            ))}
          </ul>

          {/* 分隔线与邮箱 */}
          <div className="divider my-2"></div>

          <div className="alert alert-info alert-soft dark:alert-outline mb-4 py-3 mx-2.5">
            <svg className="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <div className="flex flex-row items-center gap-2">
              <span className="text-xs font-bold opacity-70">邮箱</span>
              <span className="font-mono text-info-content dark:text-info sm:ml-auto">{checkout.email}</span>
            </div>
          </div>

          {/* 支付区域 */}
          <div className="space-y-3">
            <h4 className="font-bold text-base">支付方式</h4>
            <div className="w-full p-3 bg-base-200 rounded-lg">
              <PaymentElement id="payment-element" />
            </div>

            {/* 支付按钮 */}
            <button
              type="submit"
              disabled={isSubmitting}
              className={`btn btn-primary w-full text-base`}
            >
              ${isSubmitting ?
                <span className="loading loading-dots loading-md"></span>
                : `Pay ${checkout.total.total.amount} now`
              }
            </button>
          </div>

          {/* 消息提示 */}
          {message && (
            <div
              role="alert"
              className={`alert mt-3 ${message.toLowerCase().includes('error')
                ? 'alert-error'
                : message.toLowerCase().includes('success')
                  ? 'alert-success'
                  : 'alert-info'
                }`}
            >
              <span>{message}</span>
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

