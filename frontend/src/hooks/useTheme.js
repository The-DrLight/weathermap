import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "theme";
const THEME_COLORS = { light: "#f2f5fa", dark: "#050a17" };

function readStoredTheme() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved === "light" || saved === "dark" ? saved : null;
  } catch {
    return null;
  }
}

function systemTheme() {
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches === false ? "light" : "dark";
}

/** Light/dark theme. Defaults to the system setting until the user picks one. */
export function useTheme() {
  const [theme, setTheme] = useState(
    () => document.documentElement.getAttribute("data-theme") || readStoredTheme() || systemTheme()
  );

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", THEME_COLORS[theme]);
  }, [theme]);

  // Follow the OS setting live, but only while the user hasn't chosen explicitly.
  useEffect(() => {
    const query = window.matchMedia?.("(prefers-color-scheme: dark)");
    if (!query) return undefined;
    const onChange = (e) => {
      if (!readStoredTheme()) setTheme(e.matches ? "dark" : "light");
    };
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme((current) => {
      const next = current === "dark" ? "light" : "dark";
      try {
        localStorage.setItem(STORAGE_KEY, next);
      } catch {
        /* private mode: the choice just won't persist */
      }
      return next;
    });
  }, []);

  return { theme, toggleTheme };
}
