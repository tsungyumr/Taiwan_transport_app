import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_zh.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
      : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('zh')
  ];

  /// App 名稱
  ///
  /// In zh, this message translates to:
  /// **'交通萬事通'**
  String get appTitle;

  /// 公車 Tab 標籤
  ///
  /// In zh, this message translates to:
  /// **'公車'**
  String get tabBus;

  /// 火車 Tab 標籤
  ///
  /// In zh, this message translates to:
  /// **'火車'**
  String get tabRailway;

  /// 高鐵 Tab 標籤
  ///
  /// In zh, this message translates to:
  /// **'高鐵'**
  String get tabThsr;

  /// 腳踏車 Tab 標籤
  ///
  /// In zh, this message translates to:
  /// **'腳踏車'**
  String get tabBike;

  /// 公車頁面標題
  ///
  /// In zh, this message translates to:
  /// **'大台北公車'**
  String get busTitle;

  /// 公車搜尋提示
  ///
  /// In zh, this message translates to:
  /// **'搜尋公車路線（如：307、藍1）'**
  String get busSearchHint;

  /// 公車功能副標題
  ///
  /// In zh, this message translates to:
  /// **'查詢台北市、新北平市公車路線'**
  String get busSubtitle;

  /// 清除觀看歷史按鈕
  ///
  /// In zh, this message translates to:
  /// **'清除觀看歷史'**
  String get busClearHistory;

  /// 清除歷史確認對話框標題
  ///
  /// In zh, this message translates to:
  /// **'清除觀看歷史'**
  String get busClearHistoryConfirmTitle;

  /// 清除歷史確認對話框內容
  ///
  /// In zh, this message translates to:
  /// **'確定要清除所有路線觀看記錄嗎？'**
  String get busClearHistoryConfirmContent;

  /// 歷史清除成功提示
  ///
  /// In zh, this message translates to:
  /// **'觀看歷史已清除'**
  String get busHistoryCleared;

  /// 觀看統計文字
  ///
  /// In zh, this message translates to:
  /// **'已記錄 {count} 條常看路線'**
  String busViewCount(int count);

  /// 顏色指示說明
  ///
  /// In zh, this message translates to:
  /// **'顏色越深 = 越常觀看'**
  String get busColorIndicator;

  /// 找不到路線提示
  ///
  /// In zh, this message translates to:
  /// **'找不到路線'**
  String get busNoRoutesFound;

  /// 無路線資料提示
  ///
  /// In zh, this message translates to:
  /// **'目前沒有可用的公車路線資料'**
  String get busNoRoutesEmpty;

  /// 搜尋無結果提示
  ///
  /// In zh, this message translates to:
  /// **'沒有符合 \"{query}\" 的路線'**
  String busNoRoutesSearch(String query);

  /// 清除搜尋按鈕
  ///
  /// In zh, this message translates to:
  /// **'清除搜尋'**
  String get busClearSearch;

  /// 重新載入按鈕
  ///
  /// In zh, this message translates to:
  /// **'重新載入'**
  String get busReload;

  /// 清除歷史按鈕提示
  ///
  /// In zh, this message translates to:
  /// **'清除觀看歷史'**
  String get busTooltipClearHistory;

  /// 台鐵頁面標題
  ///
  /// In zh, this message translates to:
  /// **'台鐵時刻表'**
  String get railwayTitle;

  /// 出發縣市標籤
  ///
  /// In zh, this message translates to:
  /// **'出發縣市'**
  String get railwayFromCity;

  /// 出發站標籤
  ///
  /// In zh, this message translates to:
  /// **'出發站'**
  String get railwayFromStation;

  /// 抵達縣市標籤
  ///
  /// In zh, this message translates to:
  /// **'抵達縣市'**
  String get railwayToCity;

  /// 抵達站標籤
  ///
  /// In zh, this message translates to:
  /// **'抵達站'**
  String get railwayToStation;

  /// 全部縣市選項
  ///
  /// In zh, this message translates to:
  /// **'全部縣市'**
  String get railwayAllCities;

  /// 請選擇出發站提示
  ///
  /// In zh, this message translates to:
  /// **'請選擇出發站'**
  String get railwaySelectFromStation;

  /// 請選擇抵達站提示
  ///
  /// In zh, this message translates to:
  /// **'請選擇抵達站'**
  String get railwaySelectToStation;

  /// 當天選項
  ///
  /// In zh, this message translates to:
  /// **'當天'**
  String get railwayToday;

  /// 自訂時間選項
  ///
  /// In zh, this message translates to:
  /// **'自訂時間'**
  String get railwayCustomTime;

  /// 出發日期標籤
  ///
  /// In zh, this message translates to:
  /// **'出發日期'**
  String get railwayDepartureDate;

  /// 時間範圍標籤
  ///
  /// In zh, this message translates to:
  /// **'時間範圍'**
  String get railwayTimeRange;

  /// 起始時間標籤
  ///
  /// In zh, this message translates to:
  /// **'起始'**
  String get railwayStart;

  /// 結束時間標籤
  ///
  /// In zh, this message translates to:
  /// **'結束'**
  String get railwayEnd;

  /// 車種篩選標籤
  ///
  /// In zh, this message translates to:
  /// **'車種篩選'**
  String get railwayTrainTypeFilter;

  /// 全部車種
  ///
  /// In zh, this message translates to:
  /// **'全部'**
  String get railwayTrainTypeAll;

  /// 自強號車種
  ///
  /// In zh, this message translates to:
  /// **'自強號'**
  String get railwayTrainTypeExpress;

  /// 莒光號車種
  ///
  /// In zh, this message translates to:
  /// **'莒光號'**
  String get railwayTrainTypeChuKuang;

  /// 區間車車種
  ///
  /// In zh, this message translates to:
  /// **'區間車'**
  String get railwayTrainTypeLocal;

  /// 區間快車車種
  ///
  /// In zh, this message translates to:
  /// **'區間快車'**
  String get railwayTrainTypeLocalFast;

  /// 太魯閣號車種
  ///
  /// In zh, this message translates to:
  /// **'太魯閣號'**
  String get railwayTrainTypeTaroko;

  /// 普悠瑪號車種
  ///
  /// In zh, this message translates to:
  /// **'普悠瑪號'**
  String get railwayTrainTypePuyuma;

  /// 查詢時刻表按鈕
  ///
  /// In zh, this message translates to:
  /// **'查詢時刻表'**
  String get railwaySearchButton;

  /// 找到班次統計
  ///
  /// In zh, this message translates to:
  /// **'找到 {count} 班次'**
  String railwayTrainsFound(int count);

  /// 空狀態標題
  ///
  /// In zh, this message translates to:
  /// **'請選擇站點並查詢時刻表'**
  String get railwayEmptyTitle;

  /// 空狀態副標題
  ///
  /// In zh, this message translates to:
  /// **'選擇出發站與抵達站，查看台鐵班次資訊'**
  String get railwayEmptySubtitle;

  /// 選擇站點錯誤提示
  ///
  /// In zh, this message translates to:
  /// **'請選擇出發站與抵達站'**
  String get railwaySelectStationsError;

  /// 搜尋條件標題
  ///
  /// In zh, this message translates to:
  /// **'搜尋條件'**
  String get railwaySearchConditions;

  /// 全天時間範圍
  ///
  /// In zh, this message translates to:
  /// **'全天'**
  String get railwayAllDay;

  /// 高鐵頁面標題
  ///
  /// In zh, this message translates to:
  /// **'台灣高鐵'**
  String get thsrTitle;

  /// 查詢時刻表按鈕
  ///
  /// In zh, this message translates to:
  /// **'查詢時刻表'**
  String get thsrSearchButton;

  /// 找到班次統計
  ///
  /// In zh, this message translates to:
  /// **'找到 {count} 班次'**
  String thsrTrainsFound(int count);

  /// 空狀態標題
  ///
  /// In zh, this message translates to:
  /// **'請選擇站點並查詢時刻表'**
  String get thsrEmptyTitle;

  /// 空狀態副標題
  ///
  /// In zh, this message translates to:
  /// **'選擇出發站與抵達站，查看高鐵班次資訊'**
  String get thsrEmptySubtitle;

  /// 選擇站點錯誤提示
  ///
  /// In zh, this message translates to:
  /// **'請選擇出發站與抵達站'**
  String get thsrSelectStationsError;

  /// 商務座
  ///
  /// In zh, this message translates to:
  /// **'商務'**
  String get thsrSeatBusiness;

  /// 標準座
  ///
  /// In zh, this message translates to:
  /// **'標準'**
  String get thsrSeatStandard;

  /// 自由座
  ///
  /// In zh, this message translates to:
  /// **'自由'**
  String get thsrSeatFree;

  /// 腳踏車頁面標題
  ///
  /// In zh, this message translates to:
  /// **'YouBike 腳踏車'**
  String get bikeTitle;

  /// 腳踏車功能副標題
  ///
  /// In zh, this message translates to:
  /// **'查詢台北市、新北市 YouBike 腳踏車'**
  String get bikeSubtitle;

  /// 腳踏車搜尋提示
  ///
  /// In zh, this message translates to:
  /// **'搜尋站點或地點...'**
  String get bikeSearchHint;

  /// 取得位置中提示
  ///
  /// In zh, this message translates to:
  /// **'取得位置中...'**
  String get bikeGettingLocation;

  /// GPS 未啟用提示
  ///
  /// In zh, this message translates to:
  /// **'請開啟 GPS 定位服務'**
  String get bikeGpsDisabled;

  /// 位置權限被拒絕提示
  ///
  /// In zh, this message translates to:
  /// **'需要位置權限才能顯示附近站點'**
  String get bikePermissionDenied;

  /// 位置權限永久拒絕提示
  ///
  /// In zh, this message translates to:
  /// **'位置權限被拒絕，請在設定中開啟'**
  String get bikePermissionDeniedForever;

  /// 無法取得位置提示
  ///
  /// In zh, this message translates to:
  /// **'無法取得位置'**
  String get bikeLocationFailed;

  /// 顯示附近站點提示
  ///
  /// In zh, this message translates to:
  /// **'顯示距離您最近的 5 個站點'**
  String get bikeShowNearby;

  /// 顯示搜尋結果提示
  ///
  /// In zh, this message translates to:
  /// **'顯示符合搜尋條件的站點（依距離排序）'**
  String get bikeShowSearchResults;

  /// 重試按鈕
  ///
  /// In zh, this message translates to:
  /// **'重試'**
  String get bikeRetry;

  /// 更新位置按鈕
  ///
  /// In zh, this message translates to:
  /// **'更新位置'**
  String get bikeUpdateLocation;

  /// 導航按鈕
  ///
  /// In zh, this message translates to:
  /// **'導航'**
  String get bikeNavigate;

  /// 載入站點失敗提示
  ///
  /// In zh, this message translates to:
  /// **'載入站點失敗'**
  String get bikeLoadFailed;

  /// AI規劃功能標題
  ///
  /// In zh, this message translates to:
  /// **'AI最佳搭乘規劃'**
  String get aiPlanTitle;

  /// AI分析中提示
  ///
  /// In zh, this message translates to:
  /// **'正在分析附近交通站點...'**
  String get aiPlanAnalyzing;

  /// 規劃失敗提示
  ///
  /// In zh, this message translates to:
  /// **'規劃失敗'**
  String get aiPlanFailed;

  /// 規劃錯誤訊息
  ///
  /// In zh, this message translates to:
  /// **'規劃失敗：{error}\n\n請檢查網路連線或稍後再試。'**
  String aiPlanErrorMessage(String error);

  /// 遊戲空間功能標題
  ///
  /// In zh, this message translates to:
  /// **'遊戲空間'**
  String get gameSpaceTitle;

  /// 遊戲空間即將推出提示
  ///
  /// In zh, this message translates to:
  /// **'遊戲空間即將推出！'**
  String get gameSpaceComingSoon;

  /// 取消按鈕
  ///
  /// In zh, this message translates to:
  /// **'取消'**
  String get commonCancel;

  /// 確定按鈕
  ///
  /// In zh, this message translates to:
  /// **'確定'**
  String get commonConfirm;

  /// 清除按鈕
  ///
  /// In zh, this message translates to:
  /// **'清除'**
  String get commonClear;

  /// 搜尋按鈕
  ///
  /// In zh, this message translates to:
  /// **'搜尋'**
  String get commonSearch;

  /// 今天
  ///
  /// In zh, this message translates to:
  /// **'今天'**
  String get commonToday;

  /// 設定
  ///
  /// In zh, this message translates to:
  /// **'設定'**
  String get commonSettings;

  /// 語言設定標題
  ///
  /// In zh, this message translates to:
  /// **'語言'**
  String get commonLanguage;

  /// 選擇語言標題
  ///
  /// In zh, this message translates to:
  /// **'選擇語言'**
  String get selectLanguage;

  /// 語言設定副標題
  ///
  /// In zh, this message translates to:
  /// **'選擇您偏好的顯示語言'**
  String get languageSubtitle;

  /// App 資訊標題
  ///
  /// In zh, this message translates to:
  /// **'App 資訊'**
  String get appInfoTitle;

  /// App 名稱標籤
  ///
  /// In zh, this message translates to:
  /// **'名稱'**
  String get appInfoName;

  /// App 版本標籤
  ///
  /// In zh, this message translates to:
  /// **'版本'**
  String get appInfoVersion;

  /// 資料來源標籤
  ///
  /// In zh, this message translates to:
  /// **'資料來源'**
  String get appInfoDataSource;

  /// 資料來源值
  ///
  /// In zh, this message translates to:
  /// **'TDX 運輸資料流通服務平台'**
  String get appInfoDataSourceValue;

  /// Bike map 頁面標題
  ///
  /// In zh, this message translates to:
  /// **'地圖'**
  String get bikeMapTitle;

  /// Bike map 搜尋提示
  ///
  /// In zh, this message translates to:
  /// **'搜尋地點...'**
  String get bikeMapSearchHint;

  /// YouBike 無站點資料提示
  ///
  /// In zh, this message translates to:
  /// **'暫無站點資料'**
  String get bikeNoStations;

  /// YouBike 無資料提示
  ///
  /// In zh, this message translates to:
  /// **'目前沒有可用的 YouBike 站點資料'**
  String get bikeNoStationsData;

  /// 搜尋無結果提示
  ///
  /// In zh, this message translates to:
  /// **'沒有符合 \"{query}\" 的站點'**
  String bikeNoMatchingStations(String query);

  /// 無法取得位置提示
  ///
  /// In zh, this message translates to:
  /// **'無法取得位置'**
  String get bikeUnableGetLocation;

  /// 確認 GPS 提示
  ///
  /// In zh, this message translates to:
  /// **'請確認 GPS 已開啟並允許位置權限'**
  String get bikeCheckGps;

  /// 清除搜尋按鈕
  ///
  /// In zh, this message translates to:
  /// **'清除搜尋'**
  String get bikeClearSearch;

  /// 重試取得位置按鈕
  ///
  /// In zh, this message translates to:
  /// **'重試取得位置'**
  String get bikeRetryLocation;

  /// 重新載入按鈕
  ///
  /// In zh, this message translates to:
  /// **'重新載入'**
  String get bikeReload;

  /// 總站點數統計
  ///
  /// In zh, this message translates to:
  /// **'共 {count} 個站點'**
  String bikeTotalStations(int count);

  /// 常用站點統計
  ///
  /// In zh, this message translates to:
  /// **'已記錄 {count} 個常用站點'**
  String bikeRecordedStations(int count);

  /// 更新時間顯示
  ///
  /// In zh, this message translates to:
  /// **'更新於 {time}'**
  String bikeUpdatedAt(String time);

  /// 剛剛更新
  ///
  /// In zh, this message translates to:
  /// **'剛剛'**
  String get bikeJustNow;

  /// 分鐘前
  ///
  /// In zh, this message translates to:
  /// **'{minutes} 分鐘前'**
  String bikeMinutesAgo(int minutes);

  /// 小時前
  ///
  /// In zh, this message translates to:
  /// **'{hours} 小時前'**
  String bikeHoursAgo(int hours);

  /// 可借車輛
  ///
  /// In zh, this message translates to:
  /// **'可借'**
  String get bikeAvailable;

  /// 站點文字
  ///
  /// In zh, this message translates to:
  /// **'站點'**
  String get bikeStations;

  /// AI 規劃對話框標題
  ///
  /// In zh, this message translates to:
  /// **'AI 交通規劃'**
  String get aiPlanDialogTitle;

  /// AI 規劃對話框副標題
  ///
  /// In zh, this message translates to:
  /// **'讓 Gemini AI 幫您規劃最佳路線'**
  String get aiPlanDialogSubtitle;

  /// 出發地標籤
  ///
  /// In zh, this message translates to:
  /// **'出發地'**
  String get aiPlanFromLocation;

  /// 出發地提示
  ///
  /// In zh, this message translates to:
  /// **'輸入出發地點或抓取 GPS'**
  String get aiPlanFromHint;

  /// 目的地標籤
  ///
  /// In zh, this message translates to:
  /// **'目的地'**
  String get aiPlanToLocation;

  /// 目的地提示
  ///
  /// In zh, this message translates to:
  /// **'輸入目的地或抓取 GPS'**
  String get aiPlanToHint;

  /// 開始規劃按鈕
  ///
  /// In zh, this message translates to:
  /// **'開始規劃'**
  String get aiPlanStartButton;

  /// AI 規劃載入訊息
  ///
  /// In zh, this message translates to:
  /// **'Gemini AI 正在規劃您的路線...'**
  String get aiPlanLoadingMessage;

  /// AI 規劃載入副標題
  ///
  /// In zh, this message translates to:
  /// **'這可能需要幾秒鐘'**
  String get aiPlanLoadingSubtitle;

  /// GPS 未開啟提示
  ///
  /// In zh, this message translates to:
  /// **'請先開啟定位服務'**
  String get aiPlanGpsDisabled;

  /// 定位權限被拒提示
  ///
  /// In zh, this message translates to:
  /// **'需要定位權限才能使用此功能'**
  String get aiPlanPermissionDenied;

  /// 定位權限永久拒絕提示
  ///
  /// In zh, this message translates to:
  /// **'定位權限已被永久拒絕，請在設定中開啟'**
  String get aiPlanPermissionDeniedForever;

  /// 取得位置錯誤訊息
  ///
  /// In zh, this message translates to:
  /// **'無法取得位置：{error}'**
  String aiPlanLocationError(String error);

  /// 填寫地點提示
  ///
  /// In zh, this message translates to:
  /// **'請填寫出發地和目的地'**
  String get aiPlanFillLocation;

  /// Gemini 登入對話框標題
  ///
  /// In zh, this message translates to:
  /// **'需要登入 Gemini'**
  String get geminiLoginRequired;

  /// Gemini 登入對話框內容
  ///
  /// In zh, this message translates to:
  /// **'使用 AI 規劃功能需要先登入 Gemini。\n\n請點擊「開啟登入頁面」並在開啟的網頁中登入您的 Google 帳號。\n登入完成後請返回 App 繼續使用。'**
  String get geminiLoginMessage;

  /// 開啟登入頁面按鈕
  ///
  /// In zh, this message translates to:
  /// **'開啟登入頁面'**
  String get geminiLoginButton;

  /// Gemini 登入頁面標題
  ///
  /// In zh, this message translates to:
  /// **'登入 Gemini'**
  String get geminiLoginTitle;

  /// Gemini 登入頁面副標題
  ///
  /// In zh, this message translates to:
  /// **'登入完成後將自動返回'**
  String get geminiLoginAutoReturn;

  /// Gemini 登入完成按鈕
  ///
  /// In zh, this message translates to:
  /// **'完成'**
  String get geminiLoginComplete;

  /// 地圖選點對話框標題
  ///
  /// In zh, this message translates to:
  /// **'選擇地點'**
  String get locationPickerTitle;

  /// 地圖選點副標題
  ///
  /// In zh, this message translates to:
  /// **'點擊地圖選擇位置'**
  String get locationPickerSubtitle;

  /// 已選擇位置座標
  ///
  /// In zh, this message translates to:
  /// **'已選擇: {lat}, {lng}'**
  String locationPickerSelected(String lat, String lng);

  /// 地圖選點提示文字
  ///
  /// In zh, this message translates to:
  /// **'點擊地圖選擇位置'**
  String get locationPickerHint;

  /// 確認選擇按鈕
  ///
  /// In zh, this message translates to:
  /// **'確認選擇'**
  String get locationPickerConfirmSelection;

  /// 確認對話框標題
  ///
  /// In zh, this message translates to:
  /// **'確認選擇'**
  String get locationPickerConfirmTitle;

  /// 確認對話框訊息
  ///
  /// In zh, this message translates to:
  /// **'確定要選擇這個座標嗎？'**
  String get locationPickerConfirmMessage;

  /// 緯度標籤
  ///
  /// In zh, this message translates to:
  /// **'緯度'**
  String get locationPickerLatitude;

  /// 經度標籤
  ///
  /// In zh, this message translates to:
  /// **'經度'**
  String get locationPickerLongitude;

  /// 重新選擇按鈕
  ///
  /// In zh, this message translates to:
  /// **'重新選擇'**
  String get locationPickerReSelect;

  /// AI 規劃結果標題
  ///
  /// In zh, this message translates to:
  /// **'AI 規劃結果'**
  String get aiResultTitle;

  /// AI 規劃中標題
  ///
  /// In zh, this message translates to:
  /// **'規劃中...'**
  String get aiResultPlanning;

  /// AI 結果生成者標籤
  ///
  /// In zh, this message translates to:
  /// **'由 Gemini AI 生成'**
  String get aiResultGeneratedBy;

  /// 重新規劃按鈕
  ///
  /// In zh, this message translates to:
  /// **'重新規劃'**
  String get aiResultRetry;

  /// AI 結果載入副標題
  ///
  /// In zh, this message translates to:
  /// **'這可能需要幾秒鐘'**
  String get aiResultLoadingSubtitle;

  /// AI 結果免責聲明
  ///
  /// In zh, this message translates to:
  /// **'以上資訊由 AI 生成，實際交通狀況可能有所不同，請以現場為準。'**
  String get aiResultDisclaimer;

  /// AI 規劃預設訊息
  ///
  /// In zh, this message translates to:
  /// **'AI 正在規劃路線...'**
  String get aiResultPlanningMessage;

  /// 找不到位置訊息
  ///
  /// In zh, this message translates to:
  /// **'找不到 \"{keyword}\" 的位置'**
  String bikeLocationNotFound(String keyword);

  /// 掃碼租借訊息
  ///
  /// In zh, this message translates to:
  /// **'請使用 YouBike App 掃碼租借'**
  String get bikeScanToRent;

  /// 歸還腳踏車訊息
  ///
  /// In zh, this message translates to:
  /// **'請將腳踏車歸還至停車柱'**
  String get bikeReturnToPillar;

  /// 租借按鈕
  ///
  /// In zh, this message translates to:
  /// **'租借'**
  String get bikeRent;

  /// 還車按鈕
  ///
  /// In zh, this message translates to:
  /// **'還車'**
  String get bikeReturn;

  /// 剩餘車輛標籤
  ///
  /// In zh, this message translates to:
  /// **'剩餘車輛'**
  String get bikeAvailableBikes;

  /// 空位數標籤
  ///
  /// In zh, this message translates to:
  /// **'空位數'**
  String get bikeEmptySlots;

  /// 距離標籤
  ///
  /// In zh, this message translates to:
  /// **'距離'**
  String get bikeDistance;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'zh'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'zh':
      return AppLocalizationsZh();
  }

  throw FlutterError(
      'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
      'an issue with the localizations generation tool. Please file an issue '
      'on GitHub with a reproducible sample app and the gen-l10n configuration '
      'that was used.');
}
