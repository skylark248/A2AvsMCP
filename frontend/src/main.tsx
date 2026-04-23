import React from "react";
import ReactDOM from "react-dom/client";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { RouterProvider } from "react-router-dom";

import { router } from "./app/routes";
import { appTheme } from "./app/theme";
import { AppUiProvider } from "./app/ui/AppUiProvider";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <AppUiProvider>
        <RouterProvider router={router} />
      </AppUiProvider>
    </ThemeProvider>
  </React.StrictMode>,
);
