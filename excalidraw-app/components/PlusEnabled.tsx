import React from "react";

import { IS_PLUS_ENABLED } from "../app_constants";

// Fork: guards Excalidraw+ marketing UI. Children render only when the
// plus marketing is enabled (build arg VITE_APP_DISABLE_PLUS != "true").
// Use this instead of repeating the flag check around marketing JSX.
export const PlusEnabled: React.FC<{ children?: React.ReactNode }> = ({
  children,
}) => (IS_PLUS_ENABLED ? <>{children}</> : null);
