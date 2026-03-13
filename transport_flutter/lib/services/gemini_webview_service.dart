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

  /// 取得初始化狀態
  bool get isInitialized => _isInitialized;

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
        // 保存表單數據
        saveFormData: true,
        // 啟用 Cookie
        useOnLoadResource: true,
        // 硬體加速
        hardwareAcceleration: true,
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

    // 更全面的檢查：包括登入指示器和輸入框存在性
    final jsCode = '''
      (function() {
        const loginIndicators = [
          '登入即可開始',
          '登入後你可以',
          'Sign in to start',
          '認識 Gemini',
          '認識 Gemini：你的專屬 AI 助理',
          '試用應用程式',
          '認識 Gemini：',
          'Sign in',
          'Log in',
          '登入'
        ];

        const pageText = document.body ? document.body.innerText : '';
        let foundLoginIndicator = false;

        for (const indicator of loginIndicators) {
          if (pageText.includes(indicator)) {
            foundLoginIndicator = true;
            break;
          }
        }

        // 同時檢查是否有輸入框可用
        const inputSelectors = [
          'div[contenteditable="true"]',
          'div[role="textbox"]',
          'textarea',
          'rich-textarea'
        ];

        let hasInputBox = false;
        for (const selector of inputSelectors) {
          const elements = document.querySelectorAll(selector);
          for (const el of elements) {
            if (el.offsetParent !== null && el.getBoundingClientRect().height > 0) {
              hasInputBox = true;
              break;
            }
          }
          if (hasInputBox) break;
        }

        // 如果有輸入框且沒有登入指示器，視為已登入
        if (hasInputBox && !foundLoginIndicator) {
          return 'LOGGED_IN';
        }

        // 如果有登入指示器，視為未登入
        if (foundLoginIndicator) {
          return 'NOT_LOGGED_IN';
        }

        // 預設保守處理
        return 'UNKNOWN';
      })();
    ''';

    try {
      final result = await _webViewController!.evaluateJavascript(source: jsCode);
      if (result == 'LOGGED_IN') {
        _isLoggedIn = true;
      } else if (result == 'NOT_LOGGED_IN') {
        _isLoggedIn = false;
      }
      // UNKNOWN 時保持現狀
      debugPrint('Gemini 登入狀態: ${_isLoggedIn ? '已登入' : '未登入'} (檢測結果: $result)');
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
        debugPrint('登入畫面返回，重新載入主 WebView 頁面...');
        // 重新載入頁面以獲取新的 session/cookie
        if (_webViewController != null) {
          await _webViewController!.reload();
          // 等待頁面重新載入
          await Future.delayed(const Duration(seconds: 3));
        }
        await _checkLoginStatus();
        debugPrint('登入後狀態檢查: ${_isLoggedIn ? '已登入' : '未登入'}');
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

    // 如果明確未登入且有 context，顯示登入對話框
    if (!_isLoggedIn && context != null) {
      final loggedIn = await showLoginDialog(context);
      if (!loggedIn) {
        throw Exception('需要先登入 Gemini 才能使用 AI 規劃功能');
      }
      // 登入成功後，重新初始化 WebView以獲取新的 session
      debugPrint('登入完成，重新初始化 WebView...');
      await reset();
      // 重新檢查登入狀態
      await _checkLoginStatus();
      if (!_isLoggedIn) {
        throw Exception('登入後無法取得 session，請重試');
      }
    } else if (!_isLoggedIn && context == null) {
      throw Exception('請先在瀏覽器中登入 Gemini (gemini.google.com)');
    }
    // 如果是 UNKNOWN 狀態，繼續嘗試發送，由 JavaScript 檢查結果

    _isProcessing = true;

    try {
      // 檢查頁面是否準備好
      if (_webViewController == null) {
        throw Exception('WebView 未初始化');
      }

      // 【關鍵修改】在發送新 Prompt 前，嘗試開啟新對話（清除上下文）
      debugPrint('嘗試開啟新對話...');
      await _startNewConversation();

      // 開啟新對話後，重新注入輔助腳本
      await _injectHelperScript();

      // 等待輸入框準備好
      debugPrint('等待輸入框準備好...');
      bool inputReady = false;
      for (int i = 0; i < 10; i++) {
        final checkJs = '''
          (function() {
            const selectors = [
              'div[contenteditable="true"]',
              'div[role="textbox"]',
              'textarea',
              'rich-textarea'
            ];
            for (const selector of selectors) {
              const el = document.querySelector(selector);
              if (el && el.offsetParent !== null) return 'READY';
            }
            return 'NOT_READY';
          })();
        ''';
        final checkResult = await _webViewController!.evaluateJavascript(source: checkJs);
        if (checkResult == 'READY') {
          inputReady = true;
          break;
        }
        await Future.delayed(const Duration(milliseconds: 500));
      }

      if (!inputReady) {
        throw Exception('輸入框未準備好，請稍後再試');
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

      // 等待一下讓 Gemini 開始生成回覆
      debugPrint('等待 Gemini 開始生成回覆...');
      await Future.delayed(const Duration(seconds: 5));

      // 【關鍵修改】等待新的回覆
      final response = await _waitForNewResponse(
        timeout: const Duration(seconds: 60),
      );

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

  /// 【新增方法】嘗試開啟新對話（清除之前的上下文）
  Future<void> _startNewConversation() async {
    if (_webViewController == null) return;

    try {
      const jsCode = '''
        (function() {
          // 尋找「新對話」按鈕或選單
          const newChatSelectors = [
            'button[aria-label*="新對話"]',
            'button[aria-label*="New chat"]',
            'button[aria-label*="新的對話"]',
            '[data-test-id="new-chat-button"]',
            'button svg[path*="plus"]',
            'button svg[path*="add"]',
          ];

          for (const selector of newChatSelectors) {
            try {
              const elements = document.querySelectorAll(selector);
              for (const el of elements) {
                if (el.offsetParent !== null && el.getBoundingClientRect().height > 0) {
                  el.click();
                  console.log('已點擊新對話按鈕:', selector);
                  return 'CLICKED';
                }
              }
            } catch (e) {
              // 忽略選擇器錯誤，繼續嘗試下一個
            }
          }

          // 如果找不到新對話按鈕，嘗試導航到 gemini.google.com/app（這會重置對話）
          const currentUrl = window.location.href;
          if (!currentUrl.includes('gemini.google.com/app')) {
            window.location.href = 'https://gemini.google.com/app';
            return 'NAVIGATED';
          }

          return 'NOT_FOUND';
        })();
      ''';

      final result = await _webViewController!.evaluateJavascript(source: jsCode);
      debugPrint('開啟新對話結果: $result');

      if (result == 'NAVIGATED') {
        debugPrint('導航到新頁面，等待載入...');
        // 增加等待時間讓頁面完全載入
        await Future.delayed(const Duration(seconds: 5));
        // 重新檢查登入狀態
        await _checkLoginStatus();
      } else if (result == 'CLICKED') {
        // 給予時間讓新對話介面載入
        await Future.delayed(const Duration(seconds: 3));
      } else {
        // 即使沒找到新對話按鈕，也等待一下確保頁面穩定
        await Future.delayed(const Duration(seconds: 2));
      }
    } catch (e) {
      debugPrint('開啟新對話失敗: $e');
    }
  }

  /// 【新增方法】等待新的回覆（確保只獲取新產生的回覆）
  Future<String> _waitForNewResponse({
    required Duration timeout,
  }) async {
    final stopwatch = Stopwatch()..start();
    String lastResponse = '';
    int stableCount = 0;
    int emptyCount = 0;

    while (stopwatch.elapsed < timeout) {
      await Future.delayed(const Duration(seconds: 2));

      try {
        final jsCode = '''
          (function() {
            // 使用多種選擇器嘗試找到回覆內容
            const selectors = [
              '[data-message-author-role="model"]',
              '.model-response',
              '.response-content',
              '.markdown',
              '[data-test-id="response-content"]',
              '.conversation-turn:last-child [data-message-author-role="model"]'
            ];

            let latestMessage = null;
            let totalMessages = 0;

            // 嘗試每個選擇器
            for (const selector of selectors) {
              const elements = document.querySelectorAll(selector);
              if (elements.length > 0) {
                latestMessage = elements[elements.length - 1];
                totalMessages = elements.length;
                break;
              }
            }

            if (!latestMessage) {
              return JSON.stringify({ text: '', isGenerating: true, totalMessages: 0 });
            }

            // 獲取文字內容
            let text = latestMessage.textContent || '';

            // 如果沒有文字，嘗試獲取 innerText
            if (!text || text.trim().length === 0) {
              text = latestMessage.innerText || '';
            }

            // 檢查是否還在生成中
            const isGenerating =
              latestMessage.querySelector('.loading, .streaming, [data-streaming], .generating') !== null ||
              latestMessage.innerHTML.includes('正在生成') ||
              latestMessage.innerHTML.includes('generating') ||
              latestMessage.classList.contains('streaming') ||
              text.length < 50; // 如果文字太少，可能還在生成

            return JSON.stringify({
              text: text,
              isGenerating: isGenerating,
              totalMessages: totalMessages,
              elementFound: true
            });
          })();
        ''';

        final result = await _webViewController!.evaluateJavascript(source: jsCode);
        final data = json.decode(result.toString());
        final response = data['text']?.toString().trim() ?? '';
        final isGenerating = data['isGenerating'] == true;
        final elementFound = data['elementFound'] == true;

        debugPrint('輪詢回覆 - 找到元素: $elementFound, 生成中: $isGenerating, 長度: ${response.length}');

        // 如果還沒找到元素，繼續等待
        if (!elementFound) {
          emptyCount++;
          if (emptyCount > 10) {
            debugPrint('多次未找到回覆元素，可能頁面結構有變化');
          }
          continue;
        }

        // 如果還在生成中，繼續等待
        if (isGenerating) {
          debugPrint('回覆還在生成中...');
          continue;
        }

        // 檢查回覆是否穩定（連續兩次相同）
        if (response.isNotEmpty && response.length > 50) {
          if (response == lastResponse) {
            stableCount++;
            debugPrint('回覆穩定計數: $stableCount');
            if (stableCount >= 2) {
              debugPrint('回覆已穩定，返回結果（長度: ${response.length}）');
              return response;
            }
          } else {
            stableCount = 0;
            lastResponse = response;
            debugPrint('檢測到新回覆，長度: ${response.length}');
          }
        }
      } catch (e) {
        debugPrint('輪詢回覆錯誤: $e');
      }
    }

    if (lastResponse.isNotEmpty) {
      debugPrint('超時，返回最後回覆（長度: ${lastResponse.length}）');
      return lastResponse;
    }
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

    // 使用與主服務相同的檢查邏輯
    const jsCode = '''
      (function() {
        const loginIndicators = [
          '登入即可開始',
          '登入後你可以',
          'Sign in to start',
          '認識 Gemini',
          '認識 Gemini：你的專屬 AI 助理',
          '試用應用程式',
          '認識 Gemini：',
          'Sign in',
          'Log in',
          '登入'
        ];

        const pageText = document.body ? document.body.innerText : '';
        let foundLoginIndicator = false;

        for (const indicator of loginIndicators) {
          if (pageText.includes(indicator)) {
            foundLoginIndicator = true;
            break;
          }
        }

        // 檢查是否有輸入框可用
        const inputSelectors = [
          'div[contenteditable="true"]',
          'div[role="textbox"]',
          'textarea',
          'rich-textarea'
        ];

        let hasInputBox = false;
        for (const selector of inputSelectors) {
          const elements = document.querySelectorAll(selector);
          for (const el of elements) {
            if (el.offsetParent !== null && el.getBoundingClientRect().height > 0) {
              hasInputBox = true;
              break;
            }
          }
          if (hasInputBox) break;
        }

        if (hasInputBox && !foundLoginIndicator) {
          return 'LOGGED_IN';
        }
        if (foundLoginIndicator) {
          return 'NOT_LOGGED_IN';
        }
        return 'UNKNOWN';
      })();
    ''';

    try {
      final result = await _webViewController!.evaluateJavascript(source: jsCode);
      final isLoggedIn = result == 'LOGGED_IN';

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
      resizeToAvoidBottomInset: true, // 確保鍵盤彈出時調整視窗
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
            Expanded( // 使用 Expanded 而不是 Flexible
              child: InAppWebView(
                initialUrlRequest: URLRequest(url: WebUri('https://gemini.google.com/')),
                initialSettings: InAppWebViewSettings(
                  userAgent: 'Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                  javaScriptEnabled: true,
                  domStorageEnabled: true,
                  cacheEnabled: true,
                  // 鍵盤相關設定
                  supportZoom: true,
                  useWideViewPort: true,
                  loadWithOverviewMode: false,
                  // Cookie 和 Session
                  saveFormData: true,
                  thirdPartyCookiesEnabled: true,
                  // 硬體加速
                  hardwareAcceleration: true,
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
                // 防止輸入框跳掉
                onEnterFullscreen: (controller) {},
                onExitFullscreen: (controller) {},
              ),
            ),
          ],
        ),
      ),
    );
  }
}
