// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Chinese (`zh`).
class AppLocalizationsZh extends AppLocalizations {
  AppLocalizationsZh([String locale = 'zh']) : super(locale);

  @override
  String get appTitle => '交通萬事通';

  @override
  String get tabBus => '公車';

  @override
  String get tabRailway => '火車';

  @override
  String get tabThsr => '高鐵';

  @override
  String get tabBike => '腳踏車';

  @override
  String get busTitle => '大台北公車';

  @override
  String get busSearchHint => '搜尋公車路線（如：307、藍1）';

  @override
  String get busSubtitle => '查詢台北市、新北平市公車路線';

  @override
  String get busClearHistory => '清除觀看歷史';

  @override
  String get busClearHistoryConfirmTitle => '清除觀看歷史';

  @override
  String get busClearHistoryConfirmContent => '確定要清除所有路線觀看記錄嗎？';

  @override
  String get busHistoryCleared => '觀看歷史已清除';

  @override
  String busViewCount(int count) {
    return '已記錄 $count 條常看路線';
  }

  @override
  String get busColorIndicator => '顏色越深 = 越常觀看';

  @override
  String get busNoRoutesFound => '找不到路線';

  @override
  String get busNoRoutesEmpty => '目前沒有可用的公車路線資料';

  @override
  String busNoRoutesSearch(String query) {
    return '沒有符合 \"$query\" 的路線';
  }

  @override
  String get busClearSearch => '清除搜尋';

  @override
  String get busReload => '重新載入';

  @override
  String get busTooltipClearHistory => '清除觀看歷史';

  @override
  String get railwayTitle => '台鐵時刻表';

  @override
  String get railwayFromCity => '出發縣市';

  @override
  String get railwayFromStation => '出發站';

  @override
  String get railwayToCity => '抵達縣市';

  @override
  String get railwayToStation => '抵達站';

  @override
  String get railwayAllCities => '全部縣市';

  @override
  String get railwaySelectFromStation => '請選擇出發站';

  @override
  String get railwaySelectToStation => '請選擇抵達站';

  @override
  String get railwayToday => '當天';

  @override
  String get railwayCustomTime => '自訂時間';

  @override
  String get railwayDepartureDate => '出發日期';

  @override
  String get railwayTimeRange => '時間範圍';

  @override
  String get railwayStart => '起始';

  @override
  String get railwayEnd => '結束';

  @override
  String get railwayTrainTypeFilter => '車種篩選';

  @override
  String get railwayTrainTypeAll => '全部';

  @override
  String get railwayTrainTypeExpress => '自強號';

  @override
  String get railwayTrainTypeChuKuang => '莒光號';

  @override
  String get railwayTrainTypeLocal => '區間車';

  @override
  String get railwayTrainTypeLocalFast => '區間快車';

  @override
  String get railwayTrainTypeTaroko => '太魯閣號';

  @override
  String get railwayTrainTypePuyuma => '普悠瑪號';

  @override
  String get railwaySearchButton => '查詢時刻表';

  @override
  String railwayTrainsFound(int count) {
    return '找到 $count 班次';
  }

  @override
  String get railwayEmptyTitle => '請選擇站點並查詢時刻表';

  @override
  String get railwayEmptySubtitle => '選擇出發站與抵達站，查看台鐵班次資訊';

  @override
  String get railwaySelectStationsError => '請選擇出發站與抵達站';

  @override
  String get railwaySearchConditions => '搜尋條件';

  @override
  String get railwayAllDay => '全天';

  @override
  String get thsrTitle => '台灣高鐵';

  @override
  String get thsrSearchButton => '查詢時刻表';

  @override
  String thsrTrainsFound(int count) {
    return '找到 $count 班次';
  }

  @override
  String get thsrEmptyTitle => '請選擇站點並查詢時刻表';

  @override
  String get thsrEmptySubtitle => '選擇出發站與抵達站，查看高鐵班次資訊';

  @override
  String get thsrSelectStationsError => '請選擇出發站與抵達站';

  @override
  String get thsrSeatBusiness => '商務';

  @override
  String get thsrSeatStandard => '標準';

  @override
  String get thsrSeatFree => '自由';

  @override
  String get bikeTitle => 'YouBike 腳踏車';

  @override
  String get bikeSubtitle => '查詢台北市、新北市 YouBike 腳踏車';

  @override
  String get bikeSearchHint => '搜尋站點或地點...';

  @override
  String get bikeGettingLocation => '取得位置中...';

  @override
  String get bikeGpsDisabled => '請開啟 GPS 定位服務';

  @override
  String get bikePermissionDenied => '需要位置權限才能顯示附近站點';

  @override
  String get bikePermissionDeniedForever => '位置權限被拒絕，請在設定中開啟';

  @override
  String get bikeLocationFailed => '無法取得位置';

  @override
  String get bikeShowNearby => '顯示距離您最近的 5 個站點';

  @override
  String get bikeShowSearchResults => '顯示符合搜尋條件的站點（依距離排序）';

  @override
  String get bikeRetry => '重試';

  @override
  String get bikeUpdateLocation => '更新位置';

  @override
  String get bikeNavigate => '導航';

  @override
  String get bikeLoadFailed => '載入站點失敗';

  @override
  String get aiPlanTitle => 'AI最佳搭乘規劃';

  @override
  String get aiPlanAnalyzing => '正在分析附近交通站點...';

  @override
  String get aiPlanFailed => '規劃失敗';

  @override
  String aiPlanErrorMessage(String error) {
    return '規劃失敗：$error\n\n請檢查網路連線或稍後再試。';
  }

  @override
  String get gameSpaceTitle => '遊戲空間';

  @override
  String get gameSpaceComingSoon => '遊戲空間即將推出！';

  @override
  String get commonCancel => '取消';

  @override
  String get commonConfirm => '確定';

  @override
  String get commonClear => '清除';

  @override
  String get commonSearch => '搜尋';

  @override
  String get commonToday => '今天';

  @override
  String get commonSettings => '設定';

  @override
  String get commonLanguage => '語言';

  @override
  String get languageZh => '繁體中文';

  @override
  String get languageEn => 'English';

  @override
  String get selectLanguage => '選擇語言';

  @override
  String get languageSubtitle => '選擇您偏好的顯示語言';

  @override
  String get appInfoTitle => 'App 資訊';

  @override
  String get appInfoName => '名稱';

  @override
  String get appInfoVersion => '版本';

  @override
  String get appInfoDataSource => '資料來源';

  @override
  String get appInfoDataSourceValue => 'TDX 運輸資料流通服務平台';

  @override
  String get bikeMapTitle => '地圖';

  @override
  String get bikeMapSearchHint => '搜尋地點...';

  @override
  String get bikeNoStations => '暫無站點資料';

  @override
  String get bikeNoStationsData => '目前沒有可用的 YouBike 站點資料';

  @override
  String bikeNoMatchingStations(String query) {
    return '沒有符合 \"$query\" 的站點';
  }

  @override
  String get bikeUnableGetLocation => '無法取得位置';

  @override
  String get bikeCheckGps => '請確認 GPS 已開啟並允許位置權限';

  @override
  String get bikeClearSearch => '清除搜尋';

  @override
  String get bikeRetryLocation => '重試取得位置';

  @override
  String get bikeReload => '重新載入';

  @override
  String bikeTotalStations(int count) {
    return '共 $count 個站點';
  }

  @override
  String bikeRecordedStations(int count) {
    return '已記錄 $count 個常用站點';
  }

  @override
  String bikeUpdatedAt(String time) {
    return '更新於 $time';
  }

  @override
  String get bikeJustNow => '剛剛';

  @override
  String bikeMinutesAgo(int minutes) {
    return '$minutes 分鐘前';
  }

  @override
  String bikeHoursAgo(int hours) {
    return '$hours 小時前';
  }

  @override
  String get bikeAvailable => '可借';

  @override
  String get bikeStations => '站點';

  @override
  String get aiPlanDialogTitle => 'AI 交通規劃';

  @override
  String get aiPlanDialogSubtitle => '讓 Gemini AI 幫您規劃最佳路線';

  @override
  String get aiPlanFromLocation => '出發地';

  @override
  String get aiPlanFromHint => '輸入出發地點或抓取 GPS';

  @override
  String get aiPlanToLocation => '目的地';

  @override
  String get aiPlanToHint => '輸入目的地或抓取 GPS';

  @override
  String get aiPlanStartButton => '開始規劃';

  @override
  String get aiPlanLoadingMessage => 'Gemini AI 正在規劃您的路線...';

  @override
  String get aiPlanLoadingSubtitle => '這可能需要幾秒鐘';

  @override
  String get aiPlanGpsDisabled => '請先開啟定位服務';

  @override
  String get aiPlanPermissionDenied => '需要定位權限才能使用此功能';

  @override
  String get aiPlanPermissionDeniedForever => '定位權限已被永久拒絕，請在設定中開啟';

  @override
  String aiPlanLocationError(String error) {
    return '無法取得位置：$error';
  }

  @override
  String get aiPlanFillLocation => '請填寫出發地和目的地';

  @override
  String get geminiLoginRequired => '需要登入 Gemini';

  @override
  String get geminiLoginMessage =>
      '使用 AI 規劃功能需要先登入 Gemini。\n\n請點擊「開啟登入頁面」並在開啟的網頁中登入您的 Google 帳號。\n登入完成後請返回 App 繼續使用。';

  @override
  String get geminiLoginButton => '開啟登入頁面';

  @override
  String get geminiLoginTitle => '登入 Gemini';

  @override
  String get geminiLoginAutoReturn => '登入完成後將自動返回';

  @override
  String get geminiLoginComplete => '完成';

  @override
  String get locationPickerTitle => '選擇地點';

  @override
  String get locationPickerSubtitle => '點擊地圖選擇位置';

  @override
  String locationPickerSelected(String lat, String lng) {
    return '已選擇: $lat, $lng';
  }

  @override
  String get locationPickerHint => '點擊地圖選擇位置';

  @override
  String get locationPickerConfirmSelection => '確認選擇';

  @override
  String get locationPickerConfirmTitle => '確認選擇';

  @override
  String get locationPickerConfirmMessage => '確定要選擇這個座標嗎？';

  @override
  String get locationPickerLatitude => '緯度';

  @override
  String get locationPickerLongitude => '經度';

  @override
  String get locationPickerReSelect => '重新選擇';

  @override
  String get aiResultTitle => 'AI 規劃結果';

  @override
  String get aiResultPlanning => '規劃中...';

  @override
  String get aiResultGeneratedBy => '由 Gemini AI 生成';

  @override
  String get aiResultRetry => '重新規劃';

  @override
  String get aiResultLoadingSubtitle => '這可能需要幾秒鐘';

  @override
  String get aiResultDisclaimer => '以上資訊由 AI 生成，實際交通狀況可能有所不同，請以現場為準。';

  @override
  String get aiResultPlanningMessage => 'AI 正在規劃路線...';

  @override
  String bikeLocationNotFound(String keyword) {
    return '找不到 \"$keyword\" 的位置';
  }

  @override
  String get bikeScanToRent => '請使用 YouBike App 掃碼租借';

  @override
  String get bikeReturnToPillar => '請將腳踏車歸還至停車柱';

  @override
  String get bikeRent => '租借';

  @override
  String get bikeReturn => '還車';

  @override
  String get bikeAvailableBikes => '剩餘車輛';

  @override
  String get bikeEmptySlots => '空位數';

  @override
  String get bikeDistance => '距離';
}
