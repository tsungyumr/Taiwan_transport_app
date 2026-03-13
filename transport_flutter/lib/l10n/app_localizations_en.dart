// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'Transport Guide';

  @override
  String get tabBus => 'Bus';

  @override
  String get tabRailway => 'Train';

  @override
  String get tabThsr => 'HSR';

  @override
  String get tabBike => 'Bike';

  @override
  String get busTitle => 'Taipei Bus';

  @override
  String get busSearchHint => 'Search bus routes (e.g., 307, Blue 1)';

  @override
  String get busSubtitle => 'Search Taipei and New Taipei City bus routes';

  @override
  String get busClearHistory => 'Clear View History';

  @override
  String get busClearHistoryConfirmTitle => 'Clear View History';

  @override
  String get busClearHistoryConfirmContent =>
      'Are you sure you want to clear all route view records?';

  @override
  String get busHistoryCleared => 'View history cleared';

  @override
  String busViewCount(int count) {
    return '$count frequently viewed routes recorded';
  }

  @override
  String get busColorIndicator => 'Darker color = More frequently viewed';

  @override
  String get busNoRoutesFound => 'No routes found';

  @override
  String get busNoRoutesEmpty => 'No bus route data available';

  @override
  String busNoRoutesSearch(String query) {
    return 'No routes matching \"$query\"';
  }

  @override
  String get busClearSearch => 'Clear Search';

  @override
  String get busReload => 'Reload';

  @override
  String get busTooltipClearHistory => 'Clear view history';

  @override
  String get railwayTitle => 'TRA Timetable';

  @override
  String get railwayFromCity => 'Departure City';

  @override
  String get railwayFromStation => 'From Station';

  @override
  String get railwayToCity => 'Arrival City';

  @override
  String get railwayToStation => 'To Station';

  @override
  String get railwayAllCities => 'All Cities';

  @override
  String get railwaySelectFromStation => 'Please select departure station';

  @override
  String get railwaySelectToStation => 'Please select arrival station';

  @override
  String get railwayToday => 'Today';

  @override
  String get railwayCustomTime => 'Custom Time';

  @override
  String get railwayDepartureDate => 'Departure Date';

  @override
  String get railwayTimeRange => 'Time Range';

  @override
  String get railwayStart => 'Start';

  @override
  String get railwayEnd => 'End';

  @override
  String get railwayTrainTypeFilter => 'Train Type';

  @override
  String get railwayTrainTypeAll => 'All';

  @override
  String get railwayTrainTypeExpress => 'Tze-Chiang';

  @override
  String get railwayTrainTypeChuKuang => 'Chu-Kuang';

  @override
  String get railwayTrainTypeLocal => 'Local';

  @override
  String get railwayTrainTypeLocalFast => 'Local Express';

  @override
  String get railwayTrainTypeTaroko => 'Taroko';

  @override
  String get railwayTrainTypePuyuma => 'Puyuma';

  @override
  String get railwaySearchButton => 'Search Timetable';

  @override
  String railwayTrainsFound(int count) {
    return '$count trains found';
  }

  @override
  String get railwayEmptyTitle => 'Select stations to search';

  @override
  String get railwayEmptySubtitle =>
      'Choose departure and arrival stations to view TRA schedules';

  @override
  String get railwaySelectStationsError =>
      'Please select departure and arrival stations';

  @override
  String get railwaySearchConditions => 'Search Conditions';

  @override
  String get railwayAllDay => 'All Day';

  @override
  String get thsrTitle => 'Taiwan HSR';

  @override
  String get thsrSearchButton => 'Search Timetable';

  @override
  String thsrTrainsFound(int count) {
    return '$count trains found';
  }

  @override
  String get thsrEmptyTitle => 'Select stations to search';

  @override
  String get thsrEmptySubtitle =>
      'Choose departure and arrival stations to view HSR schedules';

  @override
  String get thsrSelectStationsError =>
      'Please select departure and arrival stations';

  @override
  String get thsrSeatBusiness => 'Business';

  @override
  String get thsrSeatStandard => 'Standard';

  @override
  String get thsrSeatFree => 'Non-Reserved';

  @override
  String get bikeTitle => 'YouBike';

  @override
  String get bikeSubtitle =>
      'Search Taipei and New Taipei City YouBike stations';

  @override
  String get bikeSearchHint => 'Search stations or locations...';

  @override
  String get bikeGettingLocation => 'Getting location...';

  @override
  String get bikeGpsDisabled => 'Please enable GPS location service';

  @override
  String get bikePermissionDenied =>
      'Location permission required to show nearby stations';

  @override
  String get bikePermissionDeniedForever =>
      'Location permission denied. Please enable in settings';

  @override
  String get bikeLocationFailed => 'Unable to get location';

  @override
  String get bikeShowNearby => 'Showing 5 nearest stations to you';

  @override
  String get bikeShowSearchResults =>
      'Showing matching stations (sorted by distance)';

  @override
  String get bikeRetry => 'Retry';

  @override
  String get bikeUpdateLocation => 'Update Location';

  @override
  String get bikeNavigate => 'Navigate';

  @override
  String get bikeLoadFailed => 'Failed to load stations';

  @override
  String get aiPlanTitle => 'AI Trip Planning';

  @override
  String get aiPlanAnalyzing => 'Analyzing nearby transport stations...';

  @override
  String get aiPlanFailed => 'Planning failed';

  @override
  String aiPlanErrorMessage(String error) {
    return 'Planning failed: $error\n\nPlease check your network connection and try again.';
  }

  @override
  String get gameSpaceTitle => 'Game Space';

  @override
  String get gameSpaceComingSoon => 'Game space coming soon!';

  @override
  String get commonCancel => 'Cancel';

  @override
  String get commonConfirm => 'Confirm';

  @override
  String get commonClear => 'Clear';

  @override
  String get commonSearch => 'Search';

  @override
  String get commonToday => 'Today';

  @override
  String get commonSettings => 'Settings';

  @override
  String get commonLanguage => 'Language';

  @override
  String get languageZh => 'Traditional Chinese';

  @override
  String get languageEn => 'English';

  @override
  String get selectLanguage => 'Select Language';

  @override
  String get languageSubtitle => 'Choose your preferred display language';

  @override
  String get appInfoTitle => 'App Info';

  @override
  String get appInfoName => 'Name';

  @override
  String get appInfoVersion => 'Version';

  @override
  String get appInfoDataSource => 'Data Source';

  @override
  String get appInfoDataSourceValue => 'TDX Transport Data Exchange Platform';

  @override
  String get bikeMapTitle => 'Map';

  @override
  String get bikeMapSearchHint => 'Search location...';

  @override
  String get bikeNoStations => 'No station data available';

  @override
  String get bikeNoStationsData =>
      'No YouBike station data available currently';

  @override
  String bikeNoMatchingStations(String query) {
    return 'No stations matching \"$query\"';
  }

  @override
  String get bikeUnableGetLocation => 'Unable to get location';

  @override
  String get bikeCheckGps => 'Please enable GPS and allow location permission';

  @override
  String get bikeClearSearch => 'Clear Search';

  @override
  String get bikeRetryLocation => 'Retry Location';

  @override
  String get bikeReload => 'Reload';

  @override
  String bikeTotalStations(int count) {
    return '$count stations total';
  }

  @override
  String bikeRecordedStations(int count) {
    return '$count frequently used stations recorded';
  }

  @override
  String bikeUpdatedAt(String time) {
    return 'Updated at $time';
  }

  @override
  String get bikeJustNow => 'Just now';

  @override
  String bikeMinutesAgo(int minutes) {
    return '$minutes min ago';
  }

  @override
  String bikeHoursAgo(int hours) {
    return '$hours hr ago';
  }

  @override
  String get bikeAvailable => 'Available';

  @override
  String get bikeStations => 'Stations';

  @override
  String get aiPlanDialogTitle => 'AI Trip Planning';

  @override
  String get aiPlanDialogSubtitle =>
      'Let Gemini AI help you plan the best route';

  @override
  String get aiPlanFromLocation => 'From';

  @override
  String get aiPlanFromHint => 'Enter departure location or use GPS';

  @override
  String get aiPlanToLocation => 'To';

  @override
  String get aiPlanToHint => 'Enter destination or use GPS';

  @override
  String get aiPlanStartButton => 'Start Planning';

  @override
  String get aiPlanLoadingMessage => 'Gemini AI is planning your route...';

  @override
  String get aiPlanLoadingSubtitle => 'This may take a few seconds';

  @override
  String get aiPlanGpsDisabled => 'Please enable location services first';

  @override
  String get aiPlanPermissionDenied =>
      'Location permission required to use this feature';

  @override
  String get aiPlanPermissionDeniedForever =>
      'Location permission permanently denied, please enable in settings';

  @override
  String aiPlanLocationError(String error) {
    return 'Unable to get location: $error';
  }

  @override
  String get aiPlanFillLocation => 'Please fill in departure and destination';

  @override
  String get geminiLoginRequired => 'Login Required';

  @override
  String get geminiLoginMessage =>
      'AI planning requires Gemini login.\n\nPlease tap \"Open Login Page\" and sign in with your Google account.\nReturn to the app when done.';

  @override
  String get geminiLoginButton => 'Open Login Page';

  @override
  String get geminiLoginTitle => 'Sign in to Gemini';

  @override
  String get geminiLoginAutoReturn => 'Will auto-return after login';

  @override
  String get geminiLoginComplete => 'Done';

  @override
  String get locationPickerTitle => 'Select Location';

  @override
  String get locationPickerSubtitle => 'Tap on the map to select a location';

  @override
  String locationPickerSelected(String lat, String lng) {
    return 'Selected: $lat, $lng';
  }

  @override
  String get locationPickerHint => 'Tap on the map to select a location';

  @override
  String get locationPickerConfirmSelection => 'Confirm Selection';

  @override
  String get locationPickerConfirmTitle => 'Confirm Selection';

  @override
  String get locationPickerConfirmMessage =>
      'Are you sure you want to select these coordinates?';

  @override
  String get locationPickerLatitude => 'Latitude';

  @override
  String get locationPickerLongitude => 'Longitude';

  @override
  String get locationPickerReSelect => 'Reselect';

  @override
  String get aiResultTitle => 'AI Planning Result';

  @override
  String get aiResultPlanning => 'Planning...';

  @override
  String get aiResultGeneratedBy => 'Generated by Gemini AI';

  @override
  String get aiResultRetry => 'Retry';

  @override
  String get aiResultLoadingSubtitle => 'This may take a few seconds';

  @override
  String get aiResultDisclaimer =>
      'The above information is AI-generated. Actual traffic conditions may vary, please refer to on-site information.';

  @override
  String get aiResultPlanningMessage => 'AI is planning your route...';

  @override
  String bikeLocationNotFound(String keyword) {
    return 'Location \"$keyword\" not found';
  }

  @override
  String get bikeScanToRent => 'Please use YouBike App to scan and rent';

  @override
  String get bikeReturnToPillar =>
      'Please return the bike to the parking pillar';

  @override
  String get bikeRent => 'Rent';

  @override
  String get bikeReturn => 'Return';

  @override
  String get bikeAvailableBikes => 'Available';

  @override
  String get bikeEmptySlots => 'Empty Slots';

  @override
  String get bikeDistance => 'Distance';
}
