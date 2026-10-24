import { useEffect, useMemo, useState, type FormEvent } from "react";

type Product = { id: string; name: string; description: string; price_cents: number; tone: string };
type PaymentResponse = { status: "approved" | "declined"; incident_id?: string; order_id?: string };
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
  const [result, setResult] = useState<{ kind: "approved" | "declined"; incidentId?: string; orderId?: string } | null>(null);
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
        ? { kind: "declined", incidentId: payment.incident_id }
        : { kind: "approved", orderId: payment.order_id });
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
    setError(null);
    useApprovedCard();
  };

  return (
    <main className="store-shell">
      <header className="store-header">
        <a className="store-brand" href="/">Northstar Supply</a>
        <nav aria-label="Demo links"><a href="http://localhost:8000">On-call console</a><a href="http://localhost:8002" target="_blank" rel="noreferrer">Responder inbox</a><span>{cart.length} item{cart.length === 1 ? "" : "s"}</span></nav>
      </header>
      {error && !checkout && <p className="store-error" role="alert">{error}</p>}

      {!checkout && !result && <>
        <section className="store-hero"><p className="product-name">Local commerce demo</p><h1>Useful things for focused work.</h1><p>Browse the catalog, check out, and use a controlled payment outcome to demonstrate the complete incident workflow.</p></section>
        <section className="catalog" aria-label="Product catalog">{products.map((product) => <article className="product-card" key={product.id}><div className={`product-art ${product.tone}`} aria-hidden="true"><span>{product.name.slice(0, 1)}</span></div><div><h2>{product.name}</h2><p>{product.description}</p><div className="product-footer"><strong>{money(product.price_cents)}</strong><button type="button" onClick={() => addProduct(product)}>Add to cart</button></div></div></article>)}</section>
        <section className="cart-panel" aria-labelledby="cart-heading"><div><p className="product-name">Your cart</p><h2 id="cart-heading">Ready to check out</h2></div>{cart.length ? <div className="cart-items">{cart.map((product, index) => <div className="cart-line" key={`${product.id}-${index}`}><span>{product.name}</span><strong>{money(product.price_cents)}</strong><button type="button" onClick={() => removeProduct(index)}>Remove</button></div>)}</div> : <p className="muted">Add one product to begin the demo.</p>}<div className="cart-total"><span>Total</span><strong>{money(total)}</strong><button className="store-primary" type="button" disabled={!cart.length || !products.length} onClick={() => setCheckout(true)}>Checkout</button></div></section>
      </>}

      {checkout && !result && <section className="checkout-card"><div className="checkout-summary"><p className="product-name">Payment router</p><h1>Complete your order</h1><p>This form accepts synthetic details only. Payment fields stay inside the demo store and never enter the incident payload.</p><dl><div><dt>Items</dt><dd>{cart.length}</dd></div><div><dt>Total</dt><dd>{money(total)}</dd></div></dl></div><form onSubmit={pay}><div className="demo-choice"><button type="button" onClick={useApprovedCard}>Use approved card</button><button type="button" onClick={useDeclineCard}>Use declined card</button></div><label>Cardholder<input value={cardholder} onChange={(event) => setCardholder(event.target.value)} autoComplete="off" /></label><label>Card number<input inputMode="numeric" value={cardNumber} onChange={(event) => setCardNumber(event.target.value.replace(/\D/g, ""))} autoComplete="off" /></label><div className="field-pair"><label>Expiry<input value={expiry} onChange={(event) => setExpiry(event.target.value)} autoComplete="off" /></label><label>Security code<input inputMode="numeric" value={securityCode} onChange={(event) => setSecurityCode(event.target.value.replace(/\D/g, ""))} autoComplete="off" /></label></div>{error && <p className="store-error" role="alert">{error}</p>}<button className="store-primary pay-button" disabled={pending} type="submit">{pending ? "Processing…" : `Pay ${money(total)}`}</button><button className="text-button" type="button" onClick={() => setCheckout(false)}>Back to cart</button></form></section>}

      {result && <section className={`payment-result ${result.kind}`} aria-live="polite"><p className="product-name">Payment result</p><h1>{result.kind === "approved" ? "Payment approved" : "Payment declined"}</h1><p>{result.kind === "approved" ? "The synthetic order completed. No incident was created." : "The payment provider is unavailable. The store backend sent the failure to the on-call assistant as a real incident."}</p>{result.incidentId && <div className="incident-reference"><span>Incident ID</span><code>{result.incidentId}</code></div>}{result.orderId && <div className="incident-reference"><span>Order ID</span><code>{result.orderId}</code></div>}<div className="button-row"><a className="store-primary" href={result.incidentId ? `http://localhost:8000/?incident=${result.incidentId}` : "http://localhost:8000"}>Open on-call console</a><button type="button" onClick={reset}>Start another order</button></div></section>}
    </main>
  );
}
