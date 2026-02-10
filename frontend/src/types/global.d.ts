import { type NavigateFunction } from "react-router-dom";

declare global {
  interface Window {
    navigate: NavigateFunction; // used in utils/frontendHooks.ts
  }
}
