import { createTheme } from "@mui/material/styles";

export const appTheme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#17475f",
    },
    secondary: {
      main: "#b85c38",
    },
    background: {
      default: "#f3efe7",
      paper: "#fffdfa",
    },
  },
  shape: {
    borderRadius: 18,
  },
  typography: {
    fontFamily: '"Segoe UI", "Helvetica Neue", sans-serif',
    h1: {
      fontSize: "2.4rem",
      fontWeight: 700,
    },
    h2: {
      fontSize: "1.6rem",
      fontWeight: 700,
    },
    h3: {
      fontSize: "1.15rem",
      fontWeight: 700,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          border: "1px solid rgba(16, 32, 51, 0.08)",
          boxShadow: "0 18px 40px rgba(23, 39, 60, 0.08)",
        },
      },
    },
  },
});
