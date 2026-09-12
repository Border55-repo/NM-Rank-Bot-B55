package no.b55.nmrankbot;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import org.json.JSONObject;

public final class MainActivity extends Activity {
    private static final String GAME_URL = "https://nordicmafia.org/";
    private WebView webView;
    private TextView status;

    private static final String DOM_READER = """
        (() => {
          if (window.__nmB55Reader) { window.__nmB55Reader.scan(); return; }
          const clean = value => String(value || '').replace(/\\s+/g, ' ').trim().slice(0, 180);
          const visible = el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
          const firstText = selectors => {
            for (const selector of selectors) {
              const el = [...document.querySelectorAll(selector)].find(visible);
              if (el) return clean(el.innerText || el.textContent || el.value);
            }
            return '';
          };
          const scan = () => {
            const body = clean(document.body ? document.body.innerText : '');
            const cooldown = firstText(['#cooldown','[id*=cooldown]','[class*=cooldown]','[data-cooldown]','time']);
            const rank = firstText(['#rank','[id*=rank]','[class*=rank]']);
            const money = firstText(['#money','[id*=money]','[class*=money]']);
            const buttons = [...document.querySelectorAll('button,a,input[type=submit],input[type=button]')]
              .filter(visible).map(el => clean(el.innerText || el.value || el.title)).filter(Boolean).slice(0, 40);
            const result = {
              page: location.origin + location.pathname,
              cooldown, rank, money,
              captcha: /captcha|jeg er ikke en robot|recaptcha/i.test(body),
              jail: /sitter i fengsel|fengselstid|bryt ut/i.test(body),
              buttons
            };
            NMBridge.onObservation(JSON.stringify(result));
          };
          let timer;
          const schedule = () => { clearTimeout(timer); timer = setTimeout(scan, 400); };
          new MutationObserver(schedule).observe(document.documentElement, {subtree:true, childList:true, characterData:true, attributes:true});
          window.__nmB55Reader = { scan };
          scan();
        })();
        """;

    @SuppressLint({"SetJavaScriptEnabled", "AddJavascriptInterface"})
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(7, 17, 29));

        status = new TextView(this);
        status.setText("HTML-leser: venter på siden");
        status.setTextColor(Color.WHITE);
        status.setPadding(24, 18, 24, 18);
        root.addView(status, new LinearLayout.LayoutParams(-1, -2));

        webView = new WebView(this);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setSavePassword(false);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        webView.addJavascriptInterface(new ObservationBridge(), "NMBridge");
        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            @Override public void onPageFinished(WebView view, String url) {
                if (url != null && url.startsWith("https://nordicmafia.org/")) {
                    view.evaluateJavascript(DOM_READER, null);
                }
            }
        });
        root.addView(webView, new LinearLayout.LayoutParams(-1, 0, 1f));

        Button scan = new Button(this);
        scan.setText("Les HTML på nytt");
        scan.setOnClickListener(v -> webView.evaluateJavascript(DOM_READER, null));
        root.addView(scan, new LinearLayout.LayoutParams(-1, -2));
        setContentView(root);

        if (savedInstanceState == null) webView.loadUrl(GAME_URL);
        else webView.restoreState(savedInstanceState);
    }

    @Override protected void onSaveInstanceState(Bundle outState) {
        webView.saveState(outState);
        super.onSaveInstanceState(outState);
    }

    @Override public void onBackPressed() {
        if (webView.canGoBack()) webView.goBack(); else super.onBackPressed();
    }

    private final class ObservationBridge {
        @JavascriptInterface public void onObservation(String raw) {
            runOnUiThread(() -> {
                try {
                    JSONObject value = new JSONObject(raw);
                    String cooldown = value.optString("cooldown", "Ingen cooldown funnet");
                    String rank = value.optString("rank", "Ukjent rank");
                    String warning = value.optBoolean("captcha") ? " • CAPTCHA" : value.optBoolean("jail") ? " • Fengsel" : "";
                    status.setText("Cooldown: " + (cooldown.isEmpty() ? "klar/ukjent" : cooldown) + " • Rank: " + (rank.isEmpty() ? "ukjent" : rank) + warning);
                } catch (Exception ignored) {
                    status.setText("HTML-leser: kunne ikke tolke siden");
                }
            });
        }
    }
}

