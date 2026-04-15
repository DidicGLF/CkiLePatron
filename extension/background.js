chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'RELOAD_APP') {
    chrome.tabs.query({}, (tabs) => {
      tabs
        .filter(t => t.url && (
          t.url.startsWith('http://127.0.0.1:5000') ||
          t.url.startsWith('http://localhost:5000')
        ))
        .forEach(t => {
          chrome.scripting.executeScript({
            target: { tabId: t.id },
            func: () => window.location.reload(),
          });
        });
    });
  }
});
