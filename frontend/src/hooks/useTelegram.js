import { useState, useEffect } from 'react';

export function useTelegram() {
  const [tg, setTg] = useState(null);
  const [user, setUser] = useState(null);
  const [initData, setInitData] = useState('');

  useEffect(() => {
    // Wait for Telegram WebApp SDK to be ready
    const app = window.Telegram?.WebApp;
    if (app) {
      app.ready(); // Tell Telegram the app is ready
      setTg(app);
      setUser(app.initDataUnsafe?.user || null);
      setInitData(app.initData || '');

      // Sync Telegram theme colors to CSS variables dynamically
      if (app.themeParams) {
        const root = document.documentElement;
        if (app.themeParams.bg_color) root.style.setProperty('--tg-bg-color', app.themeParams.bg_color);
        if (app.themeParams.text_color) root.style.setProperty('--tg-text-color', app.themeParams.text_color);
        if (app.themeParams.button_color) root.style.setProperty('--tg-button-color', app.themeParams.button_color);
        if (app.themeParams.button_text_color) root.style.setProperty('--tg-button-text-color', app.themeParams.button_text_color);
      }
    }
  }, []);

  return { tg, user, initData };
}
