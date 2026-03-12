// gemini_webview_service.dart
// Gemini WebView 自動化服務
// 使用 flutter_inappwebview 在背景與 Gemini 互動

import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_inappwebview/flutter_inappwebview.dart';

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

        // 注入額外的 JavaScript 來確保頁面正常運作
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
  /// 回傳 Gemini 的回覆內容
  Future<String> sendPrompt(String prompt) async {
    if (_isProcessing) {
      throw Exception('已有規劃正在進行中，請稍候');
    }

    if (!_isInitialized) {
      await initialize();
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

      // 等待一下讓 JavaScript 執行完成（給予足夠時間處理 TrustedHTML）
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
  /// 使用更可靠的方式與 Gemini 網頁互動
  String _buildPromptInjectionJS(String prompt) {
    // 將特殊字符轉義
    final escapedPrompt = prompt
        .replaceAll(r'\', r'\\')
        .replaceAll("'", r"\'")
        .replaceAll('`', r'\`')
        .replaceAll('\n', r'\n');

    return '''
      (function() {
        // 等待頁面完全載入
        function sleep(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }

        async function sendPrompt() {
          // 尋找輸入框 - Gemini 使用 contenteditable 的 div
          const inputSelectors = [
            'div[contenteditable="true"]',
            'div[role="textbox"]',
            'textarea',
            'rich-textarea',
            '[data-test-id="input"]',
            'input-area-v2',
            'input-area'
          ];

          let inputElement = null;
          for (const selector of inputSelectors) {
            const elements = document.querySelectorAll(selector);
            for (const el of elements) {
              // 檢查元素是否可見且在視圖中
              if (el.offsetParent !== null && el.getBoundingClientRect().height > 0) {
                inputElement = el;
                break;
              }
            }
            if (inputElement) break;
          }

          if (!inputElement) {
            console.error('找不到輸入框元素');
            return 'ERROR: INPUT_NOT_FOUND';
          }

          console.log('找到輸入框:', inputElement.tagName, inputElement.className);

          // 點擊輸入框使其聚焦
          inputElement.click();
          inputElement.focus();
          await sleep(300);

          // 清空現有內容 - 使用安全的方式
          if (inputElement.value !== undefined) {
            inputElement.value = '';
          }
          // 使用 textContent 代替 innerHTML 避免 TrustedHTML 錯誤
          inputElement.textContent = '';
          // 或者使用 Range API 清空
          try {
            const range = document.createRange();
            range.selectNodeContents(inputElement);
            range.deleteContents();
          } catch (e) {
            // 如果 Range API 失敗，忽略錯誤
          }

          // 填入 Prompt - 使用更安全的方式
          const text = `$escapedPrompt`;

          // 方法1: 使用 textContent (避免 TrustedHTML 問題)
          inputElement.textContent = text;

          // 方法2: 如果 textContent 沒有作用，使用 execCommand
          if (!inputElement.textContent || inputElement.textContent.length < text.length / 2) {
            inputElement.focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('insertText', false, text);
          }

          // 方法3: 使用 Range 和 Selection API
          if (!inputElement.textContent || inputElement.textContent.length < text.length / 2) {
            const range = document.createRange();
            const sel = window.getSelection();
            range.selectNodeContents(inputElement);
            range.deleteContents();
            const textNode = document.createTextNode(text);
            range.insertNode(textNode);
            range.selectNodeContents(textNode);
            sel.removeAllRanges();
            sel.addRange(range);
          }

          // 觸發多種輸入事件
          ['input', 'change', 'keyup', 'keydown'].forEach(eventType => {
            const event = new Event(eventType, { bubbles: true, cancelable: true });
            inputElement.dispatchEvent(event);
          });

          await sleep(500);

          // 尋找提交按鈕
          const submitSelectors = [
            'button[aria-label*="傳送"]',
            'button[aria-label*="Send"]',
            'button[data-test-id="send-button"]',
            'button[aria-label*="送出"]',
            'button.send-button',
            'button.primary',
            'button[type="submit"]',
            'button svg[data-icon-name="send"]',
            'button svg[icon-name="send"]',
            'button:has(svg)',
            'button:has([name="send"])'
          ];

          let submitButton = null;
          for (const selector of submitSelectors) {
            try {
              const buttons = document.querySelectorAll(selector);
              for (const btn of buttons) {
                if (!btn.disabled && btn.offsetParent !== null) {
                  // 檢查按鈕是否在輸入框附近
                  const inputRect = inputElement.getBoundingClientRect();
                  const btnRect = btn.getBoundingClientRect();
                  const distance = Math.abs(inputRect.bottom - btnRect.top);

                  if (distance < 200) { // 在輸入框附近 200px 內
                    submitButton = btn;
                    break;
                  }
                }
              }
              if (submitButton) break;
            } catch (e) {
              // 忽略無效的選擇器
            }
          }

          if (submitButton) {
            console.log('找到提交按鈕，正在點擊...');
            submitButton.click();
            // 也嘗試觸發 mousedown 和 mouseup 事件
            submitButton.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
            submitButton.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
          } else {
            console.log('未找到提交按鈕，嘗試使用 Enter 鍵...');
            // 嘗試按 Enter 鍵
            const enterEvent = new KeyboardEvent('keydown', {
              key: 'Enter',
              code: 'Enter',
              keyCode: 13,
              which: 13,
              bubbles: true,
              cancelable: true
            });
            inputElement.dispatchEvent(enterEvent);
          }

          return 'SUCCESS';
        }

        // 執行並返回結果
        sendPrompt().then(result => {
          console.log('Prompt 發送結果:', result);
        }).catch(err => {
          console.error('發送 Prompt 時出錯:', err);
        });

        return 'SENDING...';
      })();
    ''';
  }

  /// 等待 Gemini 回覆
  /// 輪詢頁面尋找回覆內容
  Future<String> _waitForResponse({required Duration timeout}) async {
    final stopwatch = Stopwatch()..start();
    String lastResponse = '';
    int stableCount = 0;

    while (stopwatch.elapsed < timeout) {
      await Future.delayed(const Duration(seconds: 3));

      try {
        // 尋找 Gemini 回覆的 JavaScript
        final jsCode = '''
          (function() {
            // 尋找最新的回覆內容 - 使用多種選擇器
            const responseSelectors = [
              // Gemini 新版選擇器
              '.response-container .markdown',
              '.response-content',
              '.conversation-turn:last-child .content',
              '[data-test-id="response"]',
              '.message-content',
              // 通用選擇器
              '.markdown',
              '.model-response',
              '.chat-message:last-child .content',
              // 備用選擇器
              '[data-turn-index]:last-child',
              '.turn:last-child'
            ];

            let responseText = '';
            let foundElement = null;

            for (const selector of responseSelectors) {
              const elements = document.querySelectorAll(selector);
              if (elements.length > 0) {
                // 取得最後一個元素（最新的回覆）
                const element = elements[elements.length - 1];
                const text = element.textContent || element.innerText || '';
                if (text.trim() && text.trim().length > 10) {
                  responseText = text;
                  foundElement = element;
                  break;
                }
              }
            }

            // 如果沒有找到，嘗試更通用的方法
            if (!responseText) {
              // 尋找所有可能的回覆區域
              const allMessages = document.querySelectorAll('[class*="response"], [class*="message"], [class*="chat"]');
              for (const msg of allMessages) {
                const text = msg.textContent || '';
                if (text.trim() && text.length > 20) {
                  responseText = text;
                  break;
                }
              }
            }

            // 檢查是否正在生成回覆（有載入動畫）
            const isGenerating = !!document.querySelector('.generating, .loading, [data-loading="true"], .thinking, [aria-busy="true"]');

            return JSON.stringify({
              text: responseText,
              isGenerating: isGenerating,
              timestamp: Date.now()
            });
          })();
        ''';

        final result = await _webViewController!.evaluateJavascript(source: jsCode);

        if (result != null) {
          try {
            final data = json.decode(result.toString());
            final response = data['text']?.toString().trim() ?? '';
            final isGenerating = data['isGenerating'] == true;

            if (response.isNotEmpty) {
              debugPrint('輪詢回覆: 長度=${response.length}, 生成中=$isGenerating');

              if (response == lastResponse) {
                stableCount++;
                // 如果內容穩定超過 2 次且沒有在生成中，認為已完成
                if (stableCount >= 2 && !isGenerating) {
                  return response;
                }
              } else {
                stableCount = 0;
                lastResponse = response;
              }
            }
          } catch (e) {
            debugPrint('解析回覆 JSON 失敗: $e');
          }
        }
      } catch (e) {
        debugPrint('輪詢回覆時發生錯誤: $e');
      }
    }

    // 超時，返回最後收集到的回覆
    if (lastResponse.isNotEmpty) {
      return lastResponse;
    }

    throw Exception('等待回覆超時');
  }

  /// 重新載入 WebView（用於每次新的規劃）
  Future<void> reload() async {
    debugPrint('重新載入 Gemini WebView...');

    // 處理現有的 WebView
    if (_headlessWebView != null) {
      try {
        // 嘗試重新載入頁面
        if (_webViewController != null) {
          await _webViewController!.reload();
          debugPrint('WebView 已重新載入');
        }
      } catch (e) {
        debugPrint('重新載入 WebView 失敗: $e');
        // 如果重新載入失敗，重新初始化
        await dispose();
        _isInitialized = false;
        await initialize();
      }
    } else {
      // 如果 WebView 不存在，初始化
      await initialize();
    }

    // 重置處理狀態
    _isProcessing = false;
  }

  /// 完全重置 WebView（釋放資源並重新建立）
  Future<void> reset() async {
    debugPrint('完全重置 Gemini WebView...');
    await dispose();
    _isInitialized = false;
    _isProcessing = false;
    await initialize();
  }

  /// 釋放資源
  Future<void> dispose() async {
    _headlessWebView?.dispose();
    if (_responseController != null && !_responseController!.isClosed) {
      await _responseController!.close();
    }
    _isInitialized = false;
    _isProcessing = false;
  }
}

/// 用於生成 AI 規劃的 Prompt 模板
class AIPromptTemplates {
  /// 生成交通規劃 Prompt
  static String generateTransportPlanPrompt({
    required String fromLocation,
    required String toLocation,
    List<Map<String, dynamic>>? nearbyBusStops,
    List<Map<String, dynamic>>? nearbyRailwayStations,
    List<Map<String, dynamic>>? nearbyTHSRStations,
    List<Map<String, dynamic>>? nearbyBikeStations,
  }) {
    final buffer = StringBuffer();

    buffer.writeln('請幫我規劃從「$fromLocation」到「$toLocation」的最佳大眾交通工具搭乘方案。');
    buffer.writeln();

    // 添加附近交通資訊
    buffer.writeln('附近可用交通資訊：');

    if (nearbyBusStops != null && nearbyBusStops.isNotEmpty) {
      buffer.writeln('- 公車站點：${nearbyBusStops.map((s) => s['name'] ?? '未知站點').join('、')}');
    }

    if (nearbyRailwayStations != null && nearbyRailwayStations.isNotEmpty) {
      buffer.writeln('- 火車站點：${nearbyRailwayStations.map((s) => s['name'] ?? '未知站點').join('、')}');
    }

    if (nearbyTHSRStations != null && nearbyTHSRStations.isNotEmpty) {
      buffer.writeln('- 高鐵站點：${nearbyTHSRStations.map((s) => s['name'] ?? '未知站點').join('、')}');
    }

    if (nearbyBikeStations != null && nearbyBikeStations.isNotEmpty) {
      buffer.writeln('- 腳踏車站點：${nearbyBikeStations.map((s) => s['name'] ?? '未知站點').join('、')}');
    }

    buffer.writeln();
    buffer.writeln('請提供：');
    buffer.writeln('1. 推薦的交通方式組合（例如：公車轉捷運、騎腳踏車到火車站等）');
    buffer.writeln('2. 預估總時間');
    buffer.writeln('3. 轉乘建議與注意事項');
    buffer.writeln('4. 預估費用（如果有）');
    buffer.writeln('5. 備用方案（如果有的話）');

    return buffer.toString();
  }

  /// 簡化版 Prompt（無附近資訊時使用）
  static String generateSimplePrompt({
    required String fromLocation,
    required String toLocation,
  }) {
    return '''
請幫我規劃從「$fromLocation」到「$toLocation」的最佳大眾交通工具搭乘方案。

請提供：
1. 推薦的交通方式組合
2. 預估總時間
3. 轉乘建議與注意事項
4. 預估費用
5. 備用方案
'''.trim();
  }
}
