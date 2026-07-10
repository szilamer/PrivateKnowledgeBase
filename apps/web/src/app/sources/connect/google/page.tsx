import { Suspense } from "react";

import ConnectGooglePage from "./ConnectGoogleClient";

export default function GoogleConnectPageWrapper() {
  return (
    <Suspense fallback={<main className="page"><p className="muted">Betöltés…</p></main>}>
      <ConnectGooglePage />
    </Suspense>
  );
}
