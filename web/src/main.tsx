import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { App } from "./App";
import { SessionProvider } from "./data/session";
import { LangProvider } from "./i18n/lang";
import "./ui/tokens.css";
import "./ui/base.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <LangProvider>
        <SessionProvider>
          <App />
        </SessionProvider>
      </LangProvider>
    </BrowserRouter>
  </StrictMode>,
);
