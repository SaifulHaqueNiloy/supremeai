const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('supremeDesktopAPI', {
  minimizeWindow: () =>
    ipcRenderer.invoke('window:minimize'),

  maximizeWindow: () =>
    ipcRenderer.invoke('window:maximize'),

  closeWindow: () =>
    ipcRenderer.invoke('window:close'),

  getAppInfo: () =>
    ipcRenderer.invoke('app:get-info'),

  getSystemTheme: () =>
    ipcRenderer.invoke('theme:get-system'),

  setTheme: (theme) =>
    ipcRenderer.invoke('theme:set', theme),

  apiCall: ({ endpoint, method, body, headers }) =>
    ipcRenderer.invoke('api:call', { endpoint, method, body, headers }),

  onMenuAction: (callback) => {
    const handler = (_event, action) => callback(action);
    ipcRenderer.on('menu:action', handler);
    return () => ipcRenderer.removeListener('menu:action', handler);
  },
});
