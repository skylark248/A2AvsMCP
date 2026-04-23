import { CssBaseline, ThemeProvider } from "@mui/material";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";

import { appTheme } from "../app/theme";
import { AppUiProvider } from "../app/ui/AppUiProvider";

export function renderWithProviders(ui: ReactElement, route: string = "/") {
  return render(
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <AppUiProvider>
        <MemoryRouter initialEntries={[route]}>{ui}</MemoryRouter>
      </AppUiProvider>
    </ThemeProvider>,
  );
}
