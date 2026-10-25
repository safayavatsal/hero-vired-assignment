import { useEffect, useMemo, useState, type FormEvent } from "react";

type Product = { id: string; name: string; description: string; price_cents: number; tone: string };
type PaymentResponse = { status: "approved" | "declined"; order_id?: string; payment_reference?: string };
type CustomerScenario = "deployment_regression" | "disk_pressure" | "third_party_outage";
type ScenarioResponse = { status: "degraded" | "delayed" | "declined"; customer_message: string; reference: string; incident_id?: string | null };
const money = (cents: number) => `$${(cents / 100).toFixed(2)}`;

export function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<Product[]>([]);
  const [checkout, setCheckout] = useState(false);
  const [cardholder, setCardholder] = useState("Demo Shopper");
  const [cardNumber, setCardNumber] = useState("4242424242424242");
  const [expiry, setExpiry] = useState("12/30");
  const [securityCode, setSecurityCode] = useState("123");
  const [pending, setPending] = useState(false);
  const [result, setResult] = useState<{ kind: "approved" | "declined"; reference?: string } | null>(null);
  const [scenarioResult, setScenarioResult] = useState<ScenarioResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const total = useMemo(() => cart.reduce((sum, product) => sum + product.price_cents, 0), [cart]);

  useEffect(() => {
    fetch("/api/store/products")
      .then(async (response) => {
        if (!response.ok) throw new Error("The product catalog is unavailable.");
        setProducts(await response.json() as Product[]);
      })
      .catch((caught) => setError(caught instanceof Error ? caught.message : "The product catalog is unavailable."));
  }, []);

  const addProduct = (product: Product) => setCart((items) => [...items, product]);
  const removeProduct = (index: number) => setCart((items) => items.filter((_item, itemIndex) => itemIndex !== index));
  const useDeclineCard = () => setCardNumber("4111111111110002");
  const useApprovedCard = () => setCardNumber("4242424242424242");

  const beginProviderFailure = () => {
    if (!products.length) return setError("The product catalog is unavailable.");
    if (!cart.length) setCart([products[0]]);
    setScenarioResult(null);
    useDeclineCard();
    setCheckout(true);
  };

  const triggerScenario = async (scenario: CustomerScenario) => {
    if (!products.length) return setError("The product catalog is unavailable.");
    const productIds = cart.length ? cart.map((product) => product.id) : [products[0].id];
    if (!cart.length) setCart([products[0]]);
    setError(null);
    setScenarioResult(null);
    setPending(true);
    try {
      const response = await fetch(`/api/store/scenarios/${scenario}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ attempt_id: crypto.randomUUID(), product_ids: productIds }),
      });
      const body = await response.json().catch(() => ({})) as ScenarioResponse & { detail?: string };
      if (!response.ok) throw new Error(body.detail ?? "The store scenario could not be started.");
      setScenarioResult(body);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The store scenario could not be started.");
    } finally {
      setPending(false);
    }
  };

  const pay = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    if (!cart.length || !cardholder.trim() || !/^\d{12,19}$/.test(cardNumber) || !/^\d{2}\/\d{2}$/.test(expiry) || !/^\d{3,4}$/.test(securityCode)) {
      setError("Use the synthetic details shown in the form before paying.");
      return;
    }
    setPending(true);
    try {
      const response = await fetch("/api/store/payments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          attempt_id: crypto.randomUUID(),
          product_ids: cart.map((product) => product.id),
          cardholder,
          card_number: cardNumber,
          expiry,
          security_code: securityCode,
        }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => ({})) as { detail?: string };
        throw new Error(body.detail ?? "The payment router is unavailable.");
      }
      const payment = await response.json() as PaymentResponse;
      setResult(payment.status === "declined"
        ? { kind: "declined", reference: payment.payment_reference }
        : { kind: "approved", reference: payment.order_id });
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The payment simulation failed.");
    } finally {
      setPending(false);
    }
  };

  const reset = () => {
    setCart([]);
    setCheckout(false);
    setResult(null);
    setScenarioResult(null);
    setError(null);
    useApprovedCard();
  };

  return (
    <main className="store-shell">
      <header className="store-header">
        <a className="store-brand" href="/">Northstar Supply</a>
        <nav aria-label="Store status"><span>Secure demo checkout</span><span>{cart.length} item{cart.length === 1 ? "" : "s"}</span></nav>
      </header>
      {error && !checkout && <p className="store-error" role="alert">{error}</p>}

      {!checkout && !result && <>
        <section className="store-hero"><p className="product-name">Northstar Supply</p><h1>Useful things for focused work.</h1><p>Thoughtful essentials for a calmer desk, commute, and daily routine.</p></section>
        <section className="catalog" aria-label="Product catalog">{products.map((product) => <article className="product-card" key={product.id}><div className={`product-art ${product.tone}`} aria-hidden="true"><span>{product.name.slice(0, 1)}</span></div><div><h2>{product.name}</h2><p>{product.description}</p><div className="product-footer"><strong>{money(product.price_cents)}</strong><button type="button" onClick={() => addProduct(product)}>Add to cart</button></div></div></article>)}</section>
        <section className="demo-panel" aria-labelledby="demo-heading"><p className="product-name">Demo journeys</p><h2 id="demo-heading">See how the store handles a problem</h2><p className="muted">These controlled customer journeys create real incidents for the operations console while keeping internal tools out of the store.</p><div className="demo-grid"><article><span className="journey-label">Checkout</span><h3>Slow payment release</h3><p>Checkout becomes unusually slow after a release.</p><button type="button" disabled={pending} onClick={() => triggerScenario("deployment_regression")}>{pending ? "Starting…" : "Try slow checkout"}</button></article><article><span className="journey-label">Fulfillment</span><h3>Warehouse storage full</h3><p>Your order is accepted, but fulfillment is delayed by a worker issue.</p><button type="button" disabled={pending} onClick={() => triggerScenario("disk_pressure")}>{pending ? "Starting…" : "Try delayed fulfillment"}</button></article><article><span className="journey-label">Payment</span><h3>Card provider unavailable</h3><p>Continue through checkout and see a safe customer-facing decline.</p><button type="button" disabled={pending} onClick={beginProviderFailure}>Open failed checkout</button></article></div></section>
        {scenarioResult && <section className={`scenario-result ${scenarioResult.status}`} aria-live="polite"><p className="product-name">Store update</p><h2>{scenarioResult.status === "delayed" ? "Order fulfillment is delayed" : scenarioResult.status === "degraded" ? "Checkout needs attention" : "Payment could not be completed"}</h2><p>{scenarioResult.customer_message}</p><div className="incident-reference"><span>Customer reference</span><code>{scenarioResult.reference}</code></div></section>}
        <section className="cart-panel" aria-labelledby="cart-heading"><div><p className="product-name">Your cart</p><h2 id="cart-heading">Ready to check out</h2></div>{cart.length ? <div className="cart-items">{cart.map((product, index) => <div className="cart-line" key={`${product.id}-${index}`}><span>{product.name}</span><strong>{money(product.price_cents)}</strong><button type="button" onClick={() => removeProduct(index)}>Remove</button></div>)}</div> : <p className="muted">Add one product to begin the demo.</p>}<div className="cart-total"><span>Total</span><strong>{money(total)}</strong><button className="store-primary" type="button" disabled={!cart.length || !products.length} onClick={() => setCheckout(true)}>Checkout</button></div></section>
      </>}

      {checkout && !result && <section className="checkout-card"><div className="checkout-summary"><p className="product-name">Checkout</p><h1>Complete your order</h1><p>This demo accepts test details only. Payment fields are never saved with your order.</p><dl><div><dt>Items</dt><dd>{cart.length}</dd></div><div><dt>Total</dt><dd>{money(total)}</dd></div></dl></div><form onSubmit={pay}><div className="demo-choice"><button type="button" onClick={useApprovedCard}>Use approved card</button><button type="button" onClick={useDeclineCard}>Use declined card</button></div><label>Cardholder<input value={cardholder} onChange={(event) => setCardholder(event.target.value)} autoComplete="off" /></label><label>Card number<input inputMode="numeric" value={cardNumber} onChange={(event) => setCardNumber(event.target.value.replace(/\D/g, ""))} autoComplete="off" /></label><div className="field-pair"><label>Expiry<input value={expiry} onChange={(event) => setExpiry(event.target.value)} autoComplete="off" /></label><label>Security code<input inputMode="numeric" value={securityCode} onChange={(event) => setSecurityCode(event.target.value.replace(/\D/g, ""))} autoComplete="off" /></label></div>{error && <p className="store-error" role="alert">{error}</p>}<button className="store-primary pay-button" disabled={pending} type="submit">{pending ? "Processing…" : `Pay ${money(total)}`}</button><button className="text-button" type="button" onClick={() => setCheckout(false)}>Back to cart</button></form></section>}

      {result && <section className={`payment-result ${result.kind}`} aria-live="polite"><p className="product-name">Payment result</p><h1>{result.kind === "approved" ? "Payment approved" : "Payment could not be completed"}</h1><p>{result.kind === "approved" ? "Thanks — your synthetic order is confirmed." : "Your card provider is temporarily unavailable. Please try another payment method or return shortly."}</p>{result.reference && <div className="incident-reference"><span>{result.kind === "approved" ? "Order reference" : "Payment reference"}</span><code>{result.reference}</code></div>}<div className="button-row"><button className="store-primary" type="button" onClick={reset}>{result.kind === "approved" ? "Continue shopping" : "Try another payment"}</button></div></section>}
    </main>
  );
}
