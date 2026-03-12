// gemini_webview_service.dart
// Gemini WebView 自動化服務
// 使用 flutter_inappwebview 在背景與 Gemini 互動

import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';
import '../l10n/app_localizations.dart';

/// Gemini WebView 服務
/// 負責在背景 WebView 中與 Gemini AI 互動
class GeminiWebViewService {
  static final GeminiWebViewService _instance = GeminiWebViewService._internal();
  factory GeminiWebViewService() => _instance;
  GeminiWebViewService._internal();

  InAppWebViewController? _webViewController;
  HeadlessInAppWebView? _headlessWebView;

  // 狀態監聽
  StreamController<String>? _responseController;
  Stream<String>? get responseStream => _responseController?.stream;

  bool _isInitialized = false;
  bool _isProcessing = false;
  bool _isLoggedIn = false;

  /// 初始化 StreamController
  void _initStreamController() {
    // 如果已經關閉，重新創建
    if (_responseController != null && _responseController!.isClosed) {
      _responseController = null;
    }
    _responseController ??= StreamController<String>.broadcast();
  }

  // 自定義 User-Agent 偽裝成手機瀏覽器
  static const String _userAgent =
      'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36';

  // Gemini 網址
  static const String _geminiUrl = 'https://gemini.google.com/';

  /// 初始化 WebView
  Future<void> initialize() async {
    if (_isInitialized) return;

    // 確保 StreamController 已初始化
    _initStreamController();

    _headlessWebView = HeadlessInAppWebView(
      initialUrlRequest: URLRequest(url: WebUri(_geminiUrl)),
      initialSettings: InAppWebViewSettings(
        userAgent: _userAgent,
        javaScriptEnabled: true,
        domStorageEnabled: true,
        cacheEnabled: true,
        transparentBackground: true,
        // 允許混合內容
        mixedContentMode: MixedContentMode.MIXED_CONTENT_ALWAYS_ALLOW,
        // 允許縮放
        supportZoom: true,
        // 使用寬視圖
        useWideViewPort: true,
        // 載入圖片
        loadWithOverviewMode: true,
        // 允許媒體播放
        mediaPlaybackRequiresUserGesture: false,
        // 允許彈出窗口
        supportMultipleWindows: true,
        // JavaScript 可以自動開啟窗口
        javaScriptCanOpenWindowsAutomatically: true,
        // 允許第三方 Cookie
        thirdPartyCookiesEnabled: true,
      ),
      onWebViewCreated: (controller) {
        _webViewController = controller;
      },
      onLoadStart: (controller, url) {
        debugPrint('Gemini WebView 開始載入: $url');
      },
      onLoadStop: (controller, url) async {
        debugPrint('Gemini WebView 載入完成: $url');
        _isInitialized = true;

        // 檢查登入狀態
        await _checkLoginStatus();

        // 注入輔助腳本
        await _injectHelperScript();
      },
      onConsoleMessage: (controller, consoleMessage) {
        // 過濾常見的無害訊息
        final msg = consoleMessage.message ?? '';
        if (!msg.contains('Content Security Policy') &&
            !msg.contains('googletagmanager') &&
            !msg.contains('googleadservices') &&
            !msg.contains('doubleclick')) {
          debugPrint('Gemini WebView Console: ${consoleMessage.message}');
        }
      },
      onReceivedError: (controller, request, error) {
        debugPrint('Gemini WebView 錯誤: ${error.description}');
      },
    );

    await _headlessWebView?.run();

    // 等待頁面載入（給予足夠時間載入 JavaScript）
    await Future.delayed(const Duration(seconds: 5));
  }

  /// 檢查登入狀態
  Future<void> _checkLoginStatus() async {
    if (_webViewController == null) return;

    final jsCode = '''
      (function() {
        const loginIndicators = [
          '登入即可開始',
          '登入後你可以',
          'Sign in to start',
          '認識 Gemini',
          '認識 Gemini：你的專屬 AI 助理',
          '試用應用程式',
          '認識 Gemini：'
        ];

        const pageText = document.body ? document.body.innerText : '';
        for (const indicator of loginIndicators) {
          if (pageText.includes(indicator)) {
            return 'NOT_LOGGED_IN';
          }
        }
        return 'LOGGED_IN';
      })();
    ''';

    try {
      final result = await _webViewController!.evaluateJavascript(source: jsCode);
      _isLoggedIn = result != 'NOT_LOGGED_IN';
      debugPrint('Gemini 登入狀態: ${_isLoggedIn ? '已登入' : '未登入'}');
    } catch (e) {
      debugPrint('檢查登入狀態失敗: $e');
      _isLoggedIn = false;
    }
  }

  /// 顯示登入對話框
  Future<bool> showLoginDialog(BuildContext context) async {
    final l10n = AppLocalizations.of(context)!;
    final result = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        title: Text(l10n.geminiLoginRequired),
        content: Text(l10n.geminiLoginMessage),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(l10n.commonCancel),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(l10n.geminiLoginButton),
          ),
        ],
      ),
    );

    if (result == true) {
      // 顯示可見的 WebView 讓使用者登入
      final loginResult = await Navigator.push<bool>(
        context,
        MaterialPageRoute(
          builder: (context) => const GeminiLoginScreen(),
        ),
      );

      // 登入完成後重新檢查狀態
      if (loginResult == true) {
        await _checkLoginStatus();
        return _isLoggedIn;
      }
    }

    return false;
  }

  /// 注入輔助腳本，幫助頁面正常運作
  Future<void> _injectHelperScript() async {
    if (_webViewController == null) return;

    final helperScript = '''
      (function() {
        // 確保頁面可以正常運作
        window.flutter_inappwebview = window.flutter_inappwebview || {};
        window.flutter_inappwebview.callHandler = function(name, data) {
          console.log('Flutter Handler [' + name + ']:', data);
        };

        // 監聽頁面錯誤
        window.addEventListener('error', function(e) {
          console.log('Page Error:', e.message);
        });

        console.log('Helper script injected');
      })();
    ''';

    try {
      await _webViewController!.evaluateJavascript(source: helperScript);
    } catch (e) {
      debugPrint('注入輔助腳本失敗: $e');
    }
  }

  /// 發送 Prompt 到 Gemini
  /// [prompt] 要發送的提示文字
  /// [context] BuildContext 用於顯示登入對話框
  /// 回傳 Gemini 的回覆內容
  Future<String> sendPrompt(String prompt, {BuildContext? context}) async {
    if (_isProcessing) {
      throw Exception('已有規劃正在進行中，請稍候');
    }

    if (!_isInitialized) {
      await initialize();
    }

    // 檢查登入狀態
    await _checkLoginStatus();

    // 如果未登入且有 context，顯示登入對話框
    if (!_isLoggedIn && context != null) {
      final loggedIn = await showLoginDialog(context);
      if (!loggedIn) {
        throw Exception('需要先登入 Gemini 才能使用 AI 規劃功能');
      }
      // 登入成功後，重新初始化 WebView 以獲取新的 session
      debugPrint('登入完成，重新初始化 WebView...');
      await reset();
      // 重新檢查登入狀態
      await _checkLoginStatus();
      if (!_isLoggedIn) {
        throw Exception('登入後無法取得 session，請重試');
      }
    } else if (!_isLoggedIn) {
      throw Exception('請先在瀏覽器中登入 Gemini (gemini.google.com)');
    }

    _isProcessing = true;

    try {
      // 檢查頁面是否準備好
      if (_webViewController == null) {
        throw Exception('WebView 未初始化');
      }

      debugPrint('正在發送 Prompt 到 Gemini...');
      debugPrint('Prompt 內容: ${prompt.substring(0, prompt.length > 50 ? 50 : prompt.length)}...');

      // 使用 JavaScript 注入 Prompt
      final jsCode = _buildPromptInjectionJS(prompt);

      final result = await _webViewController!.evaluateJavascript(source: jsCode);
      debugPrint('JavaScript 執行結果: $result');

      // 檢查是否返回錯誤
      if (result != null && result.toString().contains('ERROR')) {
        if (result.toString().contains('NOT_LOGGED_IN')) {
          _isLoggedIn = false;
          throw Exception('請先在瀏覽器中登入 Gemini (gemini.google.com)');
        } else if (result.toString().contains('CHAT_INTERFACE_NOT_FOUND')) {
          throw Exception('無法載入 Gemini 對話介面，請檢查網路連線或稍後再試');
        } else if (result.toString().contains('INPUT_NOT_FOUND')) {
          throw Exception('找不到 Gemini 輸入框，頁面結構可能已更新');
        }
      }

      // 等待一下讓 JavaScript 執行完成
      await Future.delayed(const Duration(seconds: 3));

      // 等待回覆（輪詢方式）
      final response = await _waitForResponse(timeout: const Duration(seconds: 60));

      _isProcessing = false;
      return response;
    } catch (e) {
      _isProcessing = false;
      debugPrint('發送 Prompt 失敗: $e');
      throw Exception('發送 Prompt 失敗: $e');
    }
  }

  /// 構建注入 Prompt 的 JavaScript 代碼
  String _buildPromptInjectionJS(String prompt) {
    // 將特殊字符轉義
    final escapedPrompt = prompt
        .replaceAll(r'\', r'\\')
        .replaceAll("'", r"\'")
        .replaceAll('`', r'\`')
        .replaceAll('\n', r'\n');

    return '''
      (function() {
        function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

        async function sendPrompt() {
          // 檢查是否在登入頁面
          const loginIndicators = [
            '登入即可開始', '登入後你可以', 'Sign in to start',
            '認識 Gemini', '認識 Gemini：你的專屬 AI 助理'
          ];
          const pageText = document.body ? document.body.innerText : '';
          for (const indicator of loginIndicators) {
            if (pageText.includes(indicator)) {
              return 'ERROR: NOT_LOGGED_IN';
            }
          }

          // 尋找輸入框
          const inputSelectors = [
            'div[contenteditable="true"]',
            'div[role="textbox"]',
            'textarea',
            'rich-textarea',
            '[data-test-id="input"]'
          ];

          let inputElement = null;
          for (const selector of inputSelectors) {
            const elements = document.querySelectorAll(selector);
            for (const el of elements) {
              if (el.offsetParent !== null && el.getBoundingClientRect().height > 0) {
                inputElement = el;
                break;
              }
            }
            if (inputElement) break;
          }

          if (!inputElement) {
            return 'ERROR: INPUT_NOT_FOUND';
          }

          inputElement.click();
          inputElement.focus();
          await sleep(500);

          // 填入 Prompt
          const text = `$escapedPrompt`;
          inputElement.textContent = text;

          ['input', 'change', 'keyup'].forEach(eventType => {
            const event = new Event(eventType, { bubbles: true });
            inputElement.dispatchEvent(event);
          });

          await sleep(800);

          // 尋找提交按鈕
          const submitButton = document.querySelector('button[aria-label*="傳送"], button[aria-label*="Send"]');
          if (submitButton) {
            submitButton.click();
          } else {
            const enterEvent = new KeyboardEvent('keydown', {
              key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
            });
            inputElement.dispatchEvent(enterEvent);
          }

          return 'SUCCESS';
        }

        return sendPrompt();
      })();
    ''';
  }

  /// 等待 Gemini 回覆
  Future<String> _waitForResponse({required Duration timeout}) async {
    final stopwatch = Stopwatch()..start();
    String lastResponse = '';
    int stableCount = 0;

    while (stopwatch.elapsed < timeout) {
      await Future.delayed(const Duration(seconds: 3));

      try {
        const jsCode = '''
          (function() {
            const responseSelectors = [
              '.response-container .markdown',
              '.conversation-turn:last-child .content',
              '[data-message-author-role="model"]'
            ];

            for (const selector of responseSelectors) {
              const elements = document.querySelectorAll(selector);
              if (elements.length > 0) {
                const text = elements[elements.length - 1].textContent || '';
                if (text.trim().length > 50) {
                  return JSON.stringify({ text: text, isGenerating: false });
                }
              }
            }
            return JSON.stringify({ text: '', isGenerating: true });
          })();
        ''';

        final result = await _webViewController!.evaluateJavascript(source: jsCode);
        final data = json.decode(result.toString());
        final response = data['text']?.toString().trim() ?? '';

        if (response.isNotEmpty) {
          if (response == lastResponse) {
            stableCount++;
            if (stableCount >= 2) return response;
          } else {
            stableCount = 0;
            lastResponse = response;
          }
        }
      } catch (e) {
        debugPrint('輪詢回覆錯誤: $e');
      }
    }

    if (lastResponse.isNotEmpty) return lastResponse;
    throw Exception('等待回覆超時');
  }

  /// 完全重置 WebView
  Future<void> reset() async {
    debugPrint('重置 Gemini WebView...');
    await dispose();
    _isInitialized = false;
    _isProcessing = false;
    _isLoggedIn = false;
    await initialize();
  }

  /// 釋放資源
  Future<void> dispose() async {
    _headlessWebView?.dispose();
    _isInitialized = false;
    _isProcessing = false;
  }
}

/// Gemini 登入頁面
class GeminiLoginScreen extends StatefulWidget {
  const GeminiLoginScreen({super.key});

  @override
  State<GeminiLoginScreen> createState() => _GeminiLoginScreenState();
}

class _GeminiLoginScreenState extends State<GeminiLoginScreen> {
  InAppWebViewController? _webViewController;
  double _progress = 0;
  Timer? _loginCheckTimer;
  bool _isCheckingLogin = false;

  @override
  void dispose() {
    _loginCheckTimer?.cancel();
    super.dispose();
  }

  /// 檢查是否已登入
  Future<void> _checkLoginStatus() async {
    if (_webViewController == null || _isCheckingLogin) return;

    _isCheckingLogin = true;

    const jsCode = '''
      (function() {
        const loginIndicators = [
          '登入即可開始',
          '登入後你可以',
          'Sign in to start',
          '認識 Gemini',
          '認識 Gemini：你的專屬 AI 助理',
          '試用應用程式',
          '認識 Gemini：'
        ];

        const pageText = document.body ? document.body.innerText : '';
        for (const indicator of loginIndicators) {
          if (pageText.includes(indicator)) {
            return 'NOT_LOGGED_IN';
          }
        }
        return 'LOGGED_IN';
      })();
    ''';

    try {
      final result = await _webViewController!.evaluateJavascript(source: jsCode);
      final isLoggedIn = result != 'NOT_LOGGED_IN';

      debugPrint('登入畫面檢測狀態: ${isLoggedIn ? '已登入' : '未登入'}');

      if (isLoggedIn && mounted) {
        // 已登入，自動返回
        _loginCheckTimer?.cancel();
        Navigator.pop(context, true);
      }
    } catch (e) {
      debugPrint('檢查登入狀態失敗: $e');
    } finally {
      _isCheckingLogin = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(l10n.geminiLoginTitle),
            Text(
              l10n.geminiLoginAutoReturn,
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.normal),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () {
              _loginCheckTimer?.cancel();
              Navigator.pop(context, true);
            },
            child: Text(l10n.geminiLoginComplete, style: const TextStyle(color: Colors.white)),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            LinearProgressIndicator(value: _progress),
            Flexible(
              child: InAppWebView(
                initialUrlRequest: URLRequest(url: WebUri('https://gemini.google.com/')),
                initialSettings: InAppWebViewSettings(
                  userAgent: 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                  javaScriptEnabled: true,
                  domStorageEnabled: true,
                ),
                onWebViewCreated: (controller) {
                  _webViewController = controller;
                },
                onProgressChanged: (controller, progress) {
                  setState(() {
                    _progress = progress / 100;
                  });
                },
                onLoadStop: (controller, url) {
                  // 頁面載入完成後開始定時檢查登入狀態
                  _loginCheckTimer?.cancel();
                  _loginCheckTimer = Timer.periodic(
                    const Duration(seconds: 2),
                    (_) => _checkLoginStatus(),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
