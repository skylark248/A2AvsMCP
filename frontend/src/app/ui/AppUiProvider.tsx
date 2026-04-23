import { Alert, Snackbar } from "@mui/material";
import { createContext, useCallback, useContext, useMemo, useState } from "react";

interface AppToast {
  message: string;
  severity?: "success" | "info" | "warning" | "error";
}

interface AppUiContextValue {
  isPresentationChromeHidden: boolean;
  setPresentationChromeHidden: (value: boolean) => void;
  showToast: (toast: AppToast) => void;
}

const AppUiContext = createContext<AppUiContextValue | null>(null);

export function AppUiProvider(props: { children: React.ReactNode }) {
  const [isPresentationChromeHidden, setPresentationChromeHidden] = useState(false);
  const [toast, setToast] = useState<AppToast | null>(null);

  const showToast = useCallback((nextToast: AppToast) => {
    setToast(nextToast);
  }, []);

  const value = useMemo(
    () => ({ isPresentationChromeHidden, setPresentationChromeHidden, showToast }),
    [isPresentationChromeHidden, showToast],
  );

  return (
    <AppUiContext.Provider value={value}>
      {props.children}
      <Snackbar
        open={Boolean(toast)}
        autoHideDuration={2600}
        onClose={() => setToast(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert
          onClose={() => setToast(null)}
          severity={toast?.severity ?? "info"}
          variant="filled"
          sx={{ width: "100%" }}
        >
          {toast?.message}
        </Alert>
      </Snackbar>
    </AppUiContext.Provider>
  );
}

export function useAppUi() {
  const context = useContext(AppUiContext);
  if (!context) {
    throw new Error("useAppUi must be used within AppUiProvider.");
  }
  return context;
}
