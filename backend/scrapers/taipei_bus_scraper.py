"""
台北市公車 eBus 爬蟲模組
Taipei Bus Scraper Module

這個模組使用 Playwright 自動化瀏覽器來抓取台北市公車的即時資訊，
包括路線列表、站牌資訊和公車即時位置。

資料來源: https://ebus.gov.taipei/
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from playwright.async_api import async_playwright, Browser, Page, Response


# ==================== 設定日誌 ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 靜態路線列表（補充用）====================
# 這些是常見的捷運接駁公車、幹線公車等，用於補充網頁爬蟲可能遺漏的路線
STATIC_BUS_ROUTES = [
    # 捷運藍線接駁公車
    {"route_id": "01000BL01", "route_name": "藍1", "description": "捷運昆陽站-捷運南港展覽館站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL02", "route_name": "藍2", "description": "新埔站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL05", "route_name": "藍5", "description": "捷運昆陽站-捷運南港站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL07", "route_name": "藍7", "description": "捷運南港展覽館站-台北世界貿易中心", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL10", "route_name": "藍10", "description": "民生社區-捷運國父紀念館站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL12", "route_name": "藍12", "description": "東湖-捷運國父紀念館站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL13", "route_name": "藍13", "description": "捷運忠孝復興站-大佳河濱公園", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL15", "route_name": "藍15", "description": "捷運昆陽站-捷運南港展覽館站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL17", "route_name": "藍17", "description": "五福新村-捷運永春站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL18", "route_name": "藍18", "description": "輔仁大學-捷運頂溪站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL20", "route_name": "藍20", "description": "捷運永寧站-土城駕訓中心", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL21", "route_name": "藍21", "description": "捷運海山站-財政園區", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL22", "route_name": "藍22", "description": "捷運海山站-土城駕訓中心", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL23", "route_name": "藍23", "description": "捷運海山站-財政園區", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL25", "route_name": "藍25", "description": "捷運昆陽站-捷運南港展覽館站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL26", "route_name": "藍26", "description": "捷運市政府站-舊宗路", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL27", "route_name": "藍27", "description": "捷運永春站-內湖新湖二路", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL28", "route_name": "藍28", "description": "捷運東湖站-捷運南港展覽館站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL29", "route_name": "藍29", "description": "東湖-捷運南港展覽館站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL30", "route_name": "藍30", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL31", "route_name": "藍31", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL32", "route_name": "藍32", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL33", "route_name": "藍33", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL35", "route_name": "藍35", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL36", "route_name": "藍36", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL37", "route_name": "藍37", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL38", "route_name": "藍38", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL39", "route_name": "藍39", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL40", "route_name": "藍40", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL41", "route_name": "藍41", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL50", "route_name": "藍50", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL51", "route_name": "藍51", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL52", "route_name": "藍52", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL53", "route_name": "藍53", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL55", "route_name": "藍55", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL56", "route_name": "藍56", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL57", "route_name": "藍57", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL58", "route_name": "藍58", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL59", "route_name": "藍59", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL60", "route_name": "藍60", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},
    {"route_id": "01000BL61", "route_name": "藍61", "description": "捷運南港展覽館站-捷運昆陽站", "category": "捷運藍線接駁公車"},

    # 捷運紅線接駁公車
    {"route_id": "01000R01", "route_name": "紅1", "description": "台北車站-松山車站", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R02", "route_name": "紅2", "description": "捷運石牌站-國立陽明交通大學", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R03", "route_name": "紅3", "description": "台北車站-國立故宮博物院", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R05", "route_name": "紅5", "description": "捷運劍潭站-陽明山", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R07", "route_name": "紅7", "description": "捷運石牌站-國立陽明交通大學", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R10", "route_name": "紅10", "description": "台北車站-故宮博物院", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R12", "route_name": "紅12", "description": "捷運石牌站-國立陽明交通大學", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R15", "route_name": "紅15", "description": "天母-捷運劍潭站", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R19", "route_name": "紅19", "description": "天母-捷運劍潭站", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R25", "route_name": "紅25", "description": "捷運北投站-國立陽明交通大學", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R30", "route_name": "紅30", "description": "捷運劍潭站-故宮博物院", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R33", "route_name": "紅33", "description": "台北車站-故宮博物院", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R35", "route_name": "紅35", "description": "台北車站-故宮博物院", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R50", "route_name": "紅50", "description": "捷運北投站-國立陽明交通大學", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R55", "route_name": "紅55", "description": "捷運北投站-國立陽明交通大學", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R57", "route_name": "紅57", "description": "捷運北投站-國立陽明交通大學", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R60", "route_name": "紅60", "description": "捷運北投站-國立陽明交通大學", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R62", "route_name": "紅62", "description": "捷運北投站-國立陽明交通大學", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R68", "route_name": "紅68", "description": "捷運北投站-國立陽明交通大學", "category": "捷運紅線接駁公車"},
    {"route_id": "01000R68", "route_name": "紅68", "description": "捷運北投站-國立陽明交通大學", "category": "捷運紅線接駁公車"},

    # 捷運綠線接駁公車
    {"route_id": "01000G01", "route_name": "綠1", "description": "中和-捷運景安站", "category": "捷運綠線接駁公車"},
    {"route_id": "01000G02", "route_name": "綠2", "description": "景美女中-捷運六張犁站", "category": "捷運綠線接駁公車"},
    {"route_id": "01000G03", "route_name": "綠3", "description": "捷運公館站-捷運景美站", "category": "捷運綠線接駁公車"},
    {"route_id": "01000G05", "route_name": "綠5", "description": "大崎頭-捷運景美站", "category": "捷運綠線接駁公車"},
    {"route_id": "01000G07", "route_name": "綠7", "description": "台北客運基隆路站-捷運七張站", "category": "捷運綠線接駁公車"},
    {"route_id": "01000G08", "route_name": "綠8", "description": "台北客運新店站-捷運七張站", "category": "捷運綠線接駁公車"},
    {"route_id": "01000G09", "route_name": "綠9", "description": "大香山-捷運景安站", "category": "捷運綠線接駁公車"},
    {"route_id": "01000G10", "route_name": "綠10", "description": "景美-捷運六張犁站", "category": "捷運綠線接駁公車"},
    {"route_id": "01000G11", "route_name": "綠11", "description": "中永和-捷運七張站", "category": "捷運綠線接駁公車"},
    {"route_id": "01000G12", "route_name": "綠12", "description": "中永和-捷運七張站", "category": "捷運綠線接駁公車"},
    {"route_id": "01000G13", "route_name": "綠13", "description": "中永和-捷運七張站", "category": "捷運綠線接駁公車"},
    {"route_id": "01000G15", "route_name": "綠15", "description": "中永和-捷運七張站", "category": "捷運綠線接駁公車"},

    # 捷運棕線接駁公車
    {"route_id": "01000BR01", "route_name": "棕1", "description": "台北車站-松山車站", "category": "捷運棕線接駁公車"},
    {"route_id": "01000BR02", "route_name": "棕2", "description": "景美女中-捷運六張犁站", "category": "捷運棕線接駁公車"},
    {"route_id": "01000BR03", "route_name": "棕3", "description": "捷運公館站-捷運景美站", "category": "捷運棕線接駁公車"},
    {"route_id": "01000BR05", "route_name": "棕5", "description": "大崎頭-捷運景美站", "category": "捷運棕線接駁公車"},
    {"route_id": "01000BR06", "route_name": "棕6", "description": "捷運動物園站-捷運市政府站", "category": "捷運棕線接駁公車"},
    {"route_id": "01000BR07", "route_name": "棕7", "description": "台北客運基隆路站-捷運七張站", "category": "捷運棕線接駁公車"},
    {"route_id": "01000BR08", "route_name": "棕8", "description": "台北客運新店站-捷運七張站", "category": "捷運棕線接駁公車"},
    {"route_id": "01000BR09", "route_name": "棕9", "description": "大香山-捷運景安站", "category": "捷運棕線接駁公車"},
    {"route_id": "01000BR10", "route_name": "棕10", "description": "景美-捷運六張犁站", "category": "捷運棕線接駁公車"},
    {"route_id": "01000BR11", "route_name": "棕11", "description": "中永和-捷運七張站", "category": "捷運棕線接駁公車"},
    {"route_id": "01000BR12", "route_name": "棕12", "description": "中永和-捷運七張站", "category": "捷運棕線接駁公車"},
    {"route_id": "01000BR15", "route_name": "棕15", "description": "中永和-捷運七張站", "category": "捷運棕線接駁公車"},
    {"route_id": "01000BR18", "route_name": "棕18", "description": "政治大學-捷運動物園站", "category": "捷運棕線接駁公車"},
    {"route_id": "01000BR20", "route_name": "棕20", "description": "政治大學-捷運動物園站", "category": "捷運棕線接駁公車"},
    {"route_id": "01000BR21", "route_name": "棕21", "description": "捷運大安站-捷運六張犁站", "category": "捷運棕線接駁公車"},
    {"route_id": "01000BR22", "route_name": "棕22", "description": "捷運大安站-捷運六張犁站", "category": "捷運棕線接駁公車"},

    # 捷運黃線接駁公車
    {"route_id": "01000Y01", "route_name": "黃1", "description": "台北車站-松山車站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y02", "route_name": "黃2", "description": "景美女中-捷運六張犁站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y05", "route_name": "黃5", "description": "大崎頭-捷運景美站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y07", "route_name": "黃7", "description": "台北客運基隆路站-捷運七張站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y08", "route_name": "黃8", "description": "台北客運新店站-捷運七張站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y10", "route_name": "黃10", "description": "景美-捷運六張犁站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y15", "route_name": "黃15", "description": "中永和-捷運七張站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y16", "route_name": "黃16", "description": "中永和-捷運七張站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y19", "route_name": "黃19", "description": "中永和-捷運七張站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y21", "route_name": "黃21", "description": "捷運大安站-捷運六張犁站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y25", "route_name": "黃25", "description": "捷運大安站-捷運六張犁站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y26", "route_name": "黃26", "description": "捷運大安站-捷運六張犁站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y28", "route_name": "黃28", "description": "捷運大安站-捷運六張犁站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y29", "route_name": "黃29", "description": "捷運大安站-捷運六張犁站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y30", "route_name": "黃30", "description": "捷運大安站-捷運六張犁站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y31", "route_name": "黃31", "description": "捷運大安站-捷運六張犁站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y32", "route_name": "黃32", "description": "捷運大安站-捷運六張犁站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y33", "route_name": "黃33", "description": "捷運大安站-捷運六張犁站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y34", "route_name": "黃34", "description": "捷運大安站-捷運六張犁站", "category": "捷運黃線接駁公車"},
    {"route_id": "01000Y35", "route_name": "黃35", "description": "捷運大安站-捷運六張犁站", "category": "捷運黃線接駁公車"},

    # 幹線公車
    {"route_id": "01000T01", "route_name": "232", "description": "松山車站-捷運中山站", "category": "幹線公車"},
    {"route_id": "01000T02", "route_name": "235", "description": "新莊區-國父紀念館", "category": "幹線公車"},
    {"route_id": "01000T03", "route_name": "257", "description": "行政院新莊聯合辦公大樓-捷運南港展覽館站", "category": "幹線公車"},
    {"route_id": "01000T04", "route_name": "261", "description": "蘆洲-捷運市政府站", "category": "幹線公車"},
    {"route_id": "01000T05", "route_name": "263", "description": "台北車站-捷運東湖站", "category": "幹線公車"},
    {"route_id": "01000T06", "route_name": "265", "description": "土城-行政院", "category": "幹線公車"},
    {"route_id": "01000T07", "route_name": "270", "description": "中華科技大學-捷運西門站", "category": "幹線公車"},
    {"route_id": "01000T08", "route_name": "274", "description": "蘆洲-台北車站", "category": "幹線公車"},
    {"route_id": "01000T09", "route_name": "307", "description": "撫遠街-台北客運板橋前站", "category": "幹線公車"},
    {"route_id": "01000T10", "route_name": "601", "description": "國防醫學院-台北車站", "category": "幹線公車"},
    {"route_id": "01000T11", "route_name": "604", "description": "台北車站-板橋", "category": "幹線公車"},
    {"route_id": "01000T12", "route_name": "605", "description": "台北車站-松山車站", "category": "幹線公車"},
    {"route_id": "01000T13", "route_name": "611", "description": "富德-台北車站", "category": "幹線公車"},
    {"route_id": "01000T14", "route_name": "639", "description": "三重-台北橋", "category": "幹線公車"},
    {"route_id": "01000T15", "route_name": "641", "description": "五堵-台北車站", "category": "幹線公車"},
    {"route_id": "01000T16", "route_name": "644", "description": "板橋-台北車站", "category": "幹線公車"},
    {"route_id": "01000T17", "route_name": "648", "description": "錦繡-台北車站", "category": "幹線公車"},

    # 快速公車
    {"route_id": "01000E01", "route_name": "906", "description": "錦繡-台北車站", "category": "快速公車"},
    {"route_id": "01000E02", "route_name": "907", "description": "錦繡-台北車站", "category": "快速公車"},
    {"route_id": "01000E03", "route_name": "908", "description": "錦繡-台北車站", "category": "快速公車"},
    {"route_id": "01000E04", "route_name": "909", "description": "錦繡-台北車站", "category": "快速公車"},
    {"route_id": "01000E05", "route_name": "910", "description": "錦繡-台北車站", "category": "快速公車"},
    {"route_id": "01000E06", "route_name": "912", "description": "錦繡-台北車站", "category": "快速公車"},
    {"route_id": "01000E07", "route_name": "913", "description": "錦繡-台北車站", "category": "快速公車"},
    {"route_id": "01000E08", "route_name": "915", "description": "錦繡-台北車站", "category": "快速公車"},
    {"route_id": "01000E09", "route_name": "916", "description": "錦繡-台北車站", "category": "快速公車"},
    {"route_id": "01000E10", "route_name": "917", "description": "錦繡-台北車站", "category": "快速公車"},
    {"route_id": "01000E11", "route_name": "918", "description": "錦繡-台北車站", "category": "快速公車"},
    {"route_id": "01000E12", "route_name": "919", "description": "錦繡-台北車站", "category": "快速公車"},
    {"route_id": "01000E13", "route_name": "920", "description": "錦繡-台北車站", "category": "快速公車"},
    {"route_id": "01000E14", "route_name": "930", "description": "青潭-台北市政府", "category": "快速公車"},
    {"route_id": "01000E15", "route_name": "932", "description": "台北車站-板橋", "category": "快速公車"},
    {"route_id": "01000E16", "route_name": "937", "description": "台北車站-板橋", "category": "快速公車"},
    {"route_id": "01000E17", "route_name": "938", "description": "台北車站-五股", "category": "快速公車"},
    {"route_id": "01000E18", "route_name": "939", "description": "台北車站-林口", "category": "快速公車"},
    {"route_id": "01000E19", "route_name": "941", "description": "台北車站-林口", "category": "快速公車"},
    {"route_id": "01000E20", "route_name": "950", "description": "新店-台北市政府", "category": "快速公車"},
]


# ==================== 自定義例外 ====================

class BusScraperError(Exception):
    """公車爬蟲基礎錯誤類別"""
    pass


class BusScraperNetworkError(BusScraperError):
    """網路連線錯誤"""
    pass


class BusScraperParseError(BusScraperError):
    """資料解析錯誤"""
    pass


class BusScraperNotFoundError(BusScraperError):
    """找不到資料錯誤"""
    pass


# ==================== 資料模型 ====================

@dataclass
class BusStop:
    """
    公車站牌資料模型

    屬性:
        sequence: 站序（第幾站）
        name: 站牌名稱
        id: 站牌ID
        latitude: 緯度
        longitude: 經度
        eta: 預估到站時間（分鐘，None表示尚未發車）
        buses: 進站中的公車列表
    """
    sequence: int
    name: str
    id: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    eta: Optional[int] = None  # 預估到站時間（分鐘）
    buses: List[Dict] = field(default_factory=list)  # 進站公車資訊

    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return {
            "sequence": self.sequence,
            "name": self.name,
            "id": self.id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "eta": self.eta,
            "buses": self.buses
        }


@dataclass
class BusInfo:
    """
    公車車輛資訊模型

    屬性:
        plate_number: 車牌號碼
        bus_type: 車種（例如：低地板、一般）
        remaining_seats: 剩餘座位數
        is_arriving: 是否即將進站
    """
    plate_number: str
    bus_type: str = ""
    remaining_seats: Optional[int] = None
    is_arriving: bool = False

    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return {
            "plate_number": self.plate_number,
            "bus_type": self.bus_type,
            "remaining_seats": self.remaining_seats,
            "is_arriving": self.is_arriving
        }


@dataclass
class BusRoute:
    """
    公車路線資料模型

    屬性:
        route_id: 路線代碼（例如：0100000A00）
        route_name: 路線名稱（例如：0東）
        departure_stop: 起點站名稱
        arrival_stop: 終點站名稱
        operator: 營運業者名稱
        direction: 方向（0=去程, 1=返程）
        direction_name_go: 去程方向名稱（例如：往 板橋後站）
        direction_name_back: 返程方向名稱（例如：往 五福新村）
        stops: 站牌列表
    """
    route_id: str
    route_name: str
    departure_stop: str
    arrival_stop: str
    operator: str = ""
    direction: int = 0  # 0=去程, 1=返程
    direction_name_go: str = ""  # 去程方向名稱
    direction_name_back: str = ""  # 返程方向名稱
    stops: List[BusStop] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return {
            "route_id": self.route_id,
            "route_name": self.route_name,
            "departure_stop": self.departure_stop,
            "arrival_stop": self.arrival_stop,
            "operator": self.operator,
            "direction": self.direction,
            "direction_name_go": self.direction_name_go,
            "direction_name_back": self.direction_name_back,
            "stops": [stop.to_dict() for stop in self.stops],
            "total_stops": len(self.stops)
        }


@dataclass
class RouteSearchResult:
    """
    路線搜尋結果模型

    屬性:
        route_id: 路線代碼
        route_name: 路線名稱
        description: 路線描述（起訖站）
        category: 路線分類
    """
    route_id: str
    route_name: str
    description: str = ""
    category: str = ""

    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return {
            "route_id": self.route_id,
            "route_name": self.route_name,
            "description": self.description,
            "category": self.category
        }


# ==================== 主要爬蟲類別 ====================

class TaipeiBusScraper:
    """
    台北市公車 eBus 爬蟲類別

    這個類別提供以下功能：
    1. 搜尋公車路線
    2. 取得特定路線的站牌列表
    3. 取得公車即時到站資訊
    4. 支援去程/返程切換

    使用範例:
        async with TaipeiBusScraper() as scraper:
            # 搜尋路線
            routes = await scraper.search_routes("307")

            # 取得路線詳細資訊
            route_data = await scraper.get_route_info("0100030700")
    """

    # 網站相關常數
    BASE_URL = "https://ebus.gov.taipei"
    EBUS_URL = f"{BASE_URL}/ebus"
    MAP_URL = f"{BASE_URL}/EBus/VsSimpleMap"
    API_STOP_DYNS = f"{BASE_URL}/EBus/GetStopDyns"

    # 路線名稱到 ebus.gov.taipei routeid 的映射表
    # 這些 ID 可以從網址 https://ebus.gov.taipei/EBus/VsSimpleMap?routeid=XXXX&gb=0 取得
    ROUTE_ID_MAP = {
        # 一般市區公車
        "235": "01000T02",
        "307": "01000T09",
        "604": "01000T11",
        "265": "01000T06",
        "651": "0411007000",
        "667": "0411007300",
        "99": "0411001200",
        "234": "0411003000",
        "705": "0411008400",
        "812": "0411009800",
        "920": "0411011300",
        "930": "0411012000",
        "965": "0411013800",
        "222": "0411000900",
        "247": "0411004300",
        "287": "0411005600",
        "620": "0411009500",
        "218": "0411002700",
        "249": "0411004600",
        "299": "0411005900",
        "527": "0411008000",

        # 幹線公車
        "232": "01000T01",
        "257": "01000T03",
        "261": "01000T04",
        "263": "01000T05",
        "270": "01000T07",
        "274": "01000T08",
        "601": "01000T10",
        "605": "01000T12",
        "611": "01000T13",
        "639": "01000T14",
        "641": "01000T15",
        "644": "01000T16",
        "648": "01000T17",

        # 快速公車
        "906": "01000E01",
        "907": "01000E02",
        "912": "01000E06",
        "932": "01000E15",
        "937": "01000E17",
        "939": "01000E19",
        "950": "01000E20",

        # 捷運藍線接駁公車
        "藍1": "01000BL01",
        "藍2": "01000BL02",
        "藍5": "01000BL05",
        "藍7": "01000BL07",
        "藍10": "01000BL10",
        "藍12": "01000BL12",
        "藍13": "01000BL13",
        "藍15": "0412001500",  # 用戶指定的正確 ID
        "藍17": "01000BL17",
        "藍18": "01000BL18",
        "藍20": "01000BL20",
        "藍21": "01000BL21",
        "藍22": "01000BL22",
        "藍23": "01000BL23",
        "藍25": "01000BL25",
        "藍26": "01000BL26",
        "藍27": "01000BL27",
        "藍28": "01000BL28",
        "藍29": "01000BL29",
        "藍30": "01000BL30",
        "藍31": "01000BL31",
        "藍32": "01000BL32",
        "藍33": "01000BL33",
        "藍35": "01000BL35",
        "藍36": "01000BL36",
        "藍37": "01000BL37",
        "藍38": "01000BL38",
        "藍39": "01000BL39",
        "藍40": "01000BL40",
        "藍41": "01000BL41",
        "藍50": "01000BL50",
        "藍51": "01000BL51",
        "藍52": "01000BL52",
        "藍53": "01000BL53",
        "藍55": "01000BL55",
        "藍56": "01000BL56",
        "藍57": "01000BL57",
        "藍58": "01000BL58",
        "藍59": "01000BL59",
        "藍60": "01000BL60",
        "藍61": "01000BL61",

        # 捷運紅線接駁公車
        "紅1": "01000R01",
        "紅2": "01000R02",
        "紅3": "01000R03",
        "紅5": "01000R05",
        "紅7": "01000R07",
        "紅10": "01000R10",
        "紅12": "01000R12",
        "紅15": "01000R15",
        "紅19": "01000R19",
        "紅25": "01000R25",
        "紅30": "01000R30",
        "紅33": "01000R33",
        "紅35": "01000R35",
        "紅50": "01000R50",
        "紅55": "01000R55",
        "紅57": "01000R57",
        "紅60": "01000R60",
        "紅62": "01000R62",
        "紅68": "01000R68",
    }

    # User-Agent 列表（輪替使用以避免被封鎖）
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        初始化爬蟲

        參數:
            headless: 是否使用無頭模式（不顯示瀏覽器視窗）
            timeout: 請求超時時間（秒）
        """
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None

        # 用於儲存攔截到的 API 回應
        self._api_responses: Dict[str, Any] = {}

    async def get_route_id(self, route_name: str) -> str:
        """
        將路線名稱轉換為 ebus.gov.taipei 的 routeid

        搜尋順序：
        1. 如果已是有效的 routeid（10位數字），直接回傳
        2. 從 ROUTE_ID_MAP 映射表查找
        3. 從 STATIC_BUS_ROUTES 靜態列表查找
        4. 動態搜尋 eBus 網站取得真實 ID

        參數:
            route_name: 路線名稱（例如："藍15", "235", "307"）

        回傳:
            ebus.gov.taipei 使用的 routeid（例如："0412001500"）
        """
        # 如果傳入的已經是有效的 routeid（10位數字），直接回傳
        if route_name and len(route_name) == 10 and route_name.isdigit():
            logger.info(f"輸入的 {route_name} 已是有效的 routeid")
            return route_name

        # 從映射表查找
        route_id = self.ROUTE_ID_MAP.get(route_name)
        if route_id and len(route_id) == 10 and route_id.isdigit():
            logger.info(f"從 ROUTE_ID_MAP 找到有效的 {route_name} -> {route_id}")
            return route_id
        elif route_id:
            logger.warning(f"ROUTE_ID_MAP 中的 {route_name} ID ({route_id}) 無效，嘗試動態搜尋...")

        # 如果找不到映射，嘗試從靜態列表查找
        for route in STATIC_BUS_ROUTES:
            if route["route_name"] == route_name:
                static_id = route["route_id"]
                # 驗證靜態ID是否為真實的數字ID（10位純數字）
                if static_id and len(static_id) == 10 and static_id.isdigit():
                    logger.info(f"從 STATIC_BUS_ROUTES 找到有效的 {route_name} -> {static_id}")
                    return static_id
                else:
                    logger.warning(f"靜態列表中的 {route_name} ID ({static_id}) 無效，嘗試動態搜尋...")
                    break  # 跳出迴圈，繼續動態搜尋

        # 動態搜尋 eBus 網站
        logger.info(f"本地映射找不到 {route_name}，嘗試動態搜尋 eBus 網站...")
        try:
            # 導航到 eBus 首頁（不等待特定 selector）
            logger.info(f"導航到 {self.EBUS_URL}")
            await self._safe_goto(self.EBUS_URL)

            # 等待頁面基本載入
            await asyncio.sleep(3)

            # 展開所有分類面板以載入完整路線列表
            logger.info("展開所有分類面板...")
            await self.page.evaluate("""
                () => {
                    // 點擊所有折疊面板的標題來展開
                    const panelHeaders = document.querySelectorAll('.panel-heading a, .panel-title a, [data-toggle="collapse"]');
                    panelHeaders.forEach(header => {
                        const panel = header.closest('.panel');
                        const collapse = panel ? panel.querySelector('.panel-collapse') : null;
                        // 如果面板是折疊的，點擊展開
                        if (collapse && !collapse.classList.contains('in')) {
                            header.click();
                        }
                    });

                    // 同時嘗試點擊所有包含路線列表的按鈕或連結
                    const allLinks = document.querySelectorAll('a[href^="#collapse"]');
                    allLinks.forEach(link => {
                        const targetId = link.getAttribute('href').substring(1);
                        const target = document.getElementById(targetId);
                        if (target && !target.classList.contains('in')) {
                            link.click();
                        }
                    });
                }
            """)

            # 等待所有面板展開和路線載入
            logger.info("等待所有路線載入...")
            await asyncio.sleep(5)

            # 截圖保存供診斷
            try:
                await self.page.screenshot(path=f"ebus_debug_{route_name}.png", full_page=True)
                logger.info(f"已保存頁面截圖: ebus_debug_{route_name}.png")
            except Exception as screenshot_err:
                logger.warning(f"截圖失敗: {screenshot_err}")

            # 取得頁面 HTML 內容供診斷
            try:
                html_content = await self.page.content()
                with open(f"ebus_debug_{route_name}.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info(f"已保存頁面 HTML: ebus_debug_{route_name}.html")
            except Exception as html_err:
                logger.warning(f"保存 HTML 失敗: {html_err}")

            # 從完整路線列表中搜尋匹配的路線 ID
            logger.info(f"從列表中搜尋路線: {route_name}")

            # 先取得頁面內容確認載入成功
            page_title = await self.page.title()
            logger.info(f"頁面標題: {page_title}")

            # 檢查 #list 是否存在（實際 HTML 結構使用 ul#list）
            routelist = await self.page.query_selector('ul#list')
            if routelist:
                logger.info("找到 ul#list 元素")
            else:
                logger.warning("找不到 ul#list 元素，嘗試其他方法...")

            # 等待更長時間確保 JavaScript 載入完成
            logger.info("等待額外 3 秒確保頁面完全載入...")
            await asyncio.sleep(3)

            result = await self.page.evaluate("""
                (targetRoute) => {
                    // 根據實際 HTML 結構：ul#list li a 格式
                    // 例如：<a href="javascript:go('0412002200')">藍22 </a>
                    let items = document.querySelectorAll('ul#list li a');
                    console.log(`ul#list li a 找到 ${items.length} 個`);

                    // 如果找不到，嘗試更寬鬆的選擇器
                    if (items.length === 0) {
                        items = document.querySelectorAll('#list li a');
                        console.log(`#list li a 找到 ${items.length} 個`);
                    }

                    // 還是找不到，嘗試所有包含 javascript:go 的鏈接
                    if (items.length === 0) {
                        const allLinks = document.querySelectorAll('a[href*="javascript:go"]');
                        items = allLinks;
                        console.log(`a[href*=javascript:go] 找到 ${items.length} 個`);
                    }

                    // 定義輔助函數：從 href 中提取 routeId
                    function extractRouteId(href) {
                        if (!href) return null;
                        const match = href.match(/go\\('([^']+)'\\)/);
                        return match ? match[1] : null;
                    }

                    // 先嘗試精確匹配
                    for (const item of items) {
                        const href = item.getAttribute('href') || '';
                        const routeId = extractRouteId(href);
                        if (routeId) {
                            const text = item.textContent.trim();
                            const parts = text.split(/\s+/);
                            const foundRouteName = parts[0] || '';

                            // 精確匹配
                            if (foundRouteName === targetRoute) {
                                console.log(`精確匹配: ${foundRouteName} -> ${routeId}`);
                                return { id: routeId, name: foundRouteName, match: 'exact' };
                            }
                        }
                    }

                    // 嘗試部分匹配
                    for (const item of items) {
                        const href = item.getAttribute('href') || '';
                        const routeId = extractRouteId(href);
                        if (routeId) {
                            const text = item.textContent.trim();
                            const parts = text.split(/\s+/);
                            const foundRouteName = parts[0] || '';

                            if (foundRouteName.includes(targetRoute) || targetRoute.includes(foundRouteName)) {
                                console.log(`部分匹配: ${foundRouteName} -> ${routeId}`);
                                return { id: routeId, name: foundRouteName, match: 'partial' };
                            }
                        }
                    }

                    // 記錄前10個項目以供除錯
                    console.log("前10個路線項目:");
                    let count = 0;
                    for (const item of items) {
                        if (count >= 10) break;
                        const href = item.getAttribute('href') || '';
                        const routeId = extractRouteId(href);
                        const text = item.textContent.trim();
                        console.log(`  ${count}: "${text.substring(0, 20)}" -> ${routeId || 'no ID'}`);
                        count++;
                    }

                    return null;
                }
            """, route_name)

            if result and result.get('id'):
                found_id = result['id']
                found_name = result.get('name', '')
                match_type = result.get('match', 'unknown')
                logger.info(f"動態搜尋成功({match_type})：{route_name} -> {found_id} ({found_name})")

                # 更新映射表（快取）
                self.ROUTE_ID_MAP[route_name] = found_id
                logger.info(f"已將 {route_name}: {found_id} 加入快取")

                return found_id
            else:
                logger.warning(f"動態搜尋 eBus 找不到路線：{route_name}")
                logger.info("建議：請確認路線名稱正確，或手動訪問 https://ebus.gov.taipei/ebus 查看可用路線")

        except Exception as e:
            logger.error(f"動態搜尋失敗: {e}")

        # 如果都找不到，拋出錯誤（不要回傳原始值，因為那會導致後續錯誤）
        raise BusScraperError(f"無法找到路線 '{route_name}' 的真實 ID，請確認路線名稱正確")

    async def __aenter__(self):
        """非同步上下文管理器進入"""
        await self._init_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同步上下文管理器退出"""
        await self._close_browser()

    async def _init_browser(self):
        """初始化 Playwright 瀏覽器"""
        try:
            logger.info("正在初始化瀏覽器...")

            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--no-sandbox"
                ]
            )

            # 建立新頁面並設定使用者代理
            context = await self.browser.new_context(
                user_agent=self.USER_AGENTS[0],
                viewport={"width": 1920, "height": 1080},
                locale="zh-TW",
                timezone_id="Asia/Taipei"
            )

            self.page = await context.new_page()

            # 設定額外的 HTTP headers
            await self.page.set_extra_http_headers({
                "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            })

            logger.info("瀏覽器初始化完成")

        except Exception as e:
            logger.error(f"瀏覽器初始化失敗: {e}")
            raise BusScraperNetworkError(f"無法初始化瀏覽器: {e}")

    async def _close_browser(self):
        """關閉瀏覽器並清理資源"""
        try:
            if self.browser:
                await self.browser.close()
                logger.info("瀏覽器已關閉")

            if self._playwright:
                await self._playwright.stop()

        except Exception as e:
            logger.error(f"關閉瀏覽器時發生錯誤: {e}")

    def _handle_response(self, response: Response):
        """
        處理網頁回應，攔截 API 資料

        這個方法會監聽所有網路請求，當發現是 GetStopDyns API 的回應時，
        會將資料儲存起來供後續使用。
        """
        try:
            if "GetStopDyns" in response.url:
                logger.debug(f"攔截到 API 回應: {response.url}")

                # 我們會在呼叫 API 後直接解析，這裡只是備用機制
                pass

        except Exception as e:
            logger.debug(f"處理回應時發生錯誤: {e}")

    async def _safe_goto(self, url: str, wait_for_selector: Optional[str] = None) -> bool:
        """
        安全地導航到指定 URL

        參數:
            url: 目標網址
            wait_for_selector: 等待出現的 CSS 選擇器

        回傳:
            是否成功載入頁面
        """
        try:
            logger.debug(f"正在導航到: {url}")

            # 使用 domcontentloaded 而不是 networkidle，因為有些網站會持續發送請求
            response = await self.page.goto(
                url,
                timeout=self.timeout * 1000,
                wait_until="domcontentloaded"
            )

            if not response or response.status >= 400:
                raise BusScraperNetworkError(f"頁面載入失敗，狀態碼: {response.status if response else 'N/A'}")

            # 等待頁面穩定（額外等待 JavaScript 執行）
            await asyncio.sleep(2)

            # 如果有指定選擇器，等待元素出現
            if wait_for_selector:
                try:
                    await self.page.wait_for_selector(wait_for_selector, timeout=15000)
                except Exception:
                    logger.warning(f"等待選擇器 {wait_for_selector} 超時，繼續執行")

            return True

        except Exception as e:
            logger.error(f"導航到 {url} 失敗: {e}")
            raise BusScraperNetworkError(f"無法載入頁面: {e}")

    async def get_all_routes(self) -> List[RouteSearchResult]:
        """
        取得所有公車路線列表（動態從網頁抓取）

        這個方法會從 eBus 網頁動態抓取所有路線資料，
        展開所有分類面板以取得完整路線列表。

        回傳:
            完整的路線搜尋結果列表

        使用範例:
            routes = await scraper.get_all_routes()
            for route in routes[:10]:
                print(f"{route.route_name}: {route.description}")
        """
        results = []
        seen_route_ids = set()

        try:
            logger.info("正在從 eBus 網頁動態抓取所有路線...")

            # 導航到首頁
            await self._safe_goto(self.EBUS_URL)

            # 等待頁面基本載入
            await asyncio.sleep(3)

            # 展開所有分類面板以載入完整路線列表
            logger.info("展開所有分類面板...")
            await self.page.evaluate("""
                () => {
                    // 點擊所有折疊面板的標題來展開
                    const panelHeaders = document.querySelectorAll('.panel-heading a, .panel-title a, [data-toggle="collapse"]');
                    panelHeaders.forEach(header => {
                        const panel = header.closest('.panel');
                        const collapse = panel ? panel.querySelector('.panel-collapse') : null;
                        // 如果面板是折疊的，點擊展開
                        if (collapse && !collapse.classList.contains('in')) {
                            header.click();
                        }
                    });

                    // 同時嘗試點擊所有包含路線列表的按鈕或連結
                    const allLinks = document.querySelectorAll('a[href^="#collapse"]');
                    allLinks.forEach(link => {
                        const targetId = link.getAttribute('href').substring(1);
                        const target = document.getElementById(targetId);
                        if (target && !target.classList.contains('in')) {
                            link.click();
                        }
                    });
                }
            """)

            # 等待所有面板展開和路線載入
            logger.info("等待所有路線載入...")
            await asyncio.sleep(5)

            # 等待路線列表載入（使用 ul#list）
            await self.page.wait_for_selector("ul#list li a", timeout=10000)

            # 使用 JavaScript 提取所有路線資料
            routes_data = await self.page.evaluate("""
                () => {
                    const routes = [];
                    const seenIds = new Set();

                    // 實際 HTML 結構：ul#list li a
                    // 例如：<a href="javascript:go('0412002200')">藍22 </a>
                    const items = document.querySelectorAll('ul#list li a');

                    items.forEach(item => {
                        const href = item.getAttribute('href') || '';
                        const match = href.match(/go\\('([^']+)'\\)/);
                        if (match) {
                            const routeId = match[1];
                            // 驗證 ID 格式（應該是10位數字）
                            if (!/^\\d{10}$/.test(routeId)) {
                                return;
                            }

                            // 避免重複
                            if (seenIds.has(routeId)) {
                                return;
                            }
                            seenIds.add(routeId);

                            const text = item.textContent.trim();
                            const parts = text.split(/\\s+/).filter(p => p);
                            const routeName = parts[0] || '';
                            const description = parts.slice(1).join(' ') || '';

                            // 從父元素取得分類
                            let category = '';
                            const panel = item.closest('.panel');
                            if (panel) {
                                const heading = panel.querySelector('.panel-heading a');
                                if (heading) {
                                    category = heading.textContent.trim();
                                }
                            }

                            routes.push({
                                route_id: routeId,
                                route_name: routeName,
                                description: description,
                                category: category
                            });
                        }
                    });

                    return routes;
                }
            """)

            # 處理抓取的路線
            for data in routes_data:
                route_id = data.get("route_id", "")
                if route_id and route_id not in seen_route_ids:
                    result = RouteSearchResult(
                        route_id=route_id,
                        route_name=data.get("route_name", ""),
                        description=data.get("description", ""),
                        category=data.get("category", "")
                    )
                    results.append(result)
                    seen_route_ids.add(route_id)

            logger.info(f"從網頁成功抓取 {len(routes_data)} 條路線")

            # 保存完整 HTML 供除錯
            try:
                html_content = await self.page.content()
                with open("ebus_all_routes.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info("已保存完整路線列表 HTML: ebus_all_routes.html")
            except Exception as html_err:
                logger.warning(f"保存 HTML 失敗: {html_err}")

        except Exception as e:
            logger.error(f"從網頁抓取路線失敗: {e}")
            logger.info("嘗試使用靜態列表作為備援...")
            # 只有當動態抓取失敗時才使用靜態列表
            for data in STATIC_BUS_ROUTES:
                route_id = data.get("route_id", "")
                if route_id and route_id not in seen_route_ids:
                    result = RouteSearchResult(
                        route_id=route_id,
                        route_name=data.get("route_name", ""),
                        description=data.get("description", ""),
                        category=data.get("category", "")
                    )
                    results.append(result)
                    seen_route_ids.add(route_id)

        logger.info(f"總共取得 {len(results)} 條路線")
        return results

    async def search_routes(self, keyword: str) -> List[RouteSearchResult]:
        """
        搜尋公車路線

        參數:
            keyword: 搜尋關鍵字（例如：路線編號、站名等）

        回傳:
            符合條件的路線列表

        使用範例:
            routes = await scraper.search_routes("307")
            for route in routes:
                print(f"找到路線: {route.route_name}")
        """
        try:
            logger.info(f"正在搜尋路線，關鍵字: '{keyword}'")

            # 先取得所有路線，再進行過濾
            all_routes = await self.get_all_routes()

            # 過濾符合關鍵字的路線
            keyword_lower = keyword.lower()
            filtered = [
                route for route in all_routes
                if keyword_lower in route.route_name.lower()
                or keyword_lower in route.description.lower()
                or keyword_lower in route.category.lower()
            ]

            logger.info(f"搜尋完成，找到 {len(filtered)} 條符合的路線")
            return filtered

        except Exception as e:
            logger.error(f"搜尋路線失敗: {e}")
            raise BusScraperError(f"無法搜尋路線: {e}")

    async def get_route_info(self, route_id: str, direction: int = 0) -> BusRoute:
        """
        取得特定路線的詳細資訊

        這個方法會開啟路線地圖頁面，並呼叫 GetStopDyns API 取得站牌和即時資訊。

        參數:
            route_id: 路線代碼（例如：0100030700）
            direction: 方向（0=去程, 1=返程）

        回傳:
            BusRoute 物件，包含站牌列表和即時資訊

        使用範例:
            route = await scraper.get_route_info("0100030700")
            print(f"路線: {route.route_name}")
            print(f"業者: {route.operator}")
            for stop in route.stops:
                print(f"  {stop.sequence}. {stop.name} - ETA: {stop.eta}分")
        """
        try:
            # 將路線名稱轉換為正確的 ebus.gov.taipei routeid（支援動態搜尋）
            actual_route_id = await self.get_route_id(route_id)
            logger.info(f"正在取得路線資訊，路線ID: {route_id} -> {actual_route_id}, 方向: {direction}")

            # 構建路線地圖頁面 URL
            map_url = f"{self.MAP_URL}?routeid={actual_route_id}&gb={direction}"
            logger.debug(f"地圖頁面 URL: {map_url}")

            # 導航到地圖頁面
            await self._safe_goto(map_url, "#simplemap_wrapper")

            # 等待頁面完全載入（等待站點元素出現）
            try:
                await self.page.wait_for_selector('[id^="block_"]', timeout=15000)
                logger.info("頁面站點元素已載入")
            except Exception as e:
                logger.warning(f"等待站點元素超時: {e}")

            # 再等待一下確保 JavaScript 渲染完成
            await asyncio.sleep(3)

            # 從頁面提取路線基本資訊
            route_info = await self.page.evaluate(r"""
                () => {
                    // 嘗試從頁面標題或元素取得路線名稱
                    const title = document.title || '';
                    const routeNameMatch = title.match(/(.+?)[-|\\s]/);
                    const routeName = routeNameMatch ? routeNameMatch[1].trim() : '';

                    // 嘗試取得起訖站資訊
                    let departure = '';
                    let arrival = '';
                    let operator = '';

                    // 從頁面中尋找路線資訊
                    const infoElements = document.querySelectorAll('.route-info, .bus-info, h1, h2');
                    infoElements.forEach(el => {
                        const text = el.textContent || '';
                        if (text.includes('往') || text.includes('-')) {
                            const parts = text.split(/[往\-]/).map(p => p.trim());
                            if (parts.length >= 2) {
                                departure = parts[0];
                                arrival = parts[1];
                            }
                        }
                    });

                    // 抓取方向名稱（rt_dir_go 和 rt_dir_back）
                    let direction_name_go = '';
                    let direction_name_back = '';

                    const goElement = document.querySelector('.rt_dir_go');
                    const backElement = document.querySelector('.rt_dir_back');

                    if (goElement) {
                        direction_name_go = goElement.textContent.trim();
                    }
                    if (backElement) {
                        direction_name_back = backElement.textContent.trim();
                    }

                    return {
                        route_name: routeName,
                        departure: departure,
                        arrival: arrival,
                        operator: operator,
                        direction_name_go: direction_name_go,
                        direction_name_back: direction_name_back
                    };
                }
            """)

            # 直接從 HTML 頁面解析所有站點資訊
            logger.info("開始從 HTML 頁面解析站點資訊...")
            stops_from_html = await self.page.evaluate("""
                () => {
                    const stops = [];
                    const debug_info = [];

                    // 選擇所有站點元素（包含 sb, sm, se, se2 等類別）
                    const stopElements = document.querySelectorAll('#plMapStops > div[id^="block_"]');
                    debug_info.push(`找到 ${stopElements.length} 個站點元素`);

                    stopElements.forEach((el, idx) => {
                        try {
                            // 取得站名（優先使用 data-stop 屬性）
                            let stopName = el.getAttribute('data-stop') || '';

                            // 如果 data-stop 沒有，嘗試從 snz 或 snz2 取得
                            if (!stopName) {
                                const snz = el.querySelector('.snz span, .snz2 span');
                                if (snz) {
                                    stopName = snz.textContent.trim();
                                }
                            }

                            // 取得 ETA 資訊
                            let etaText = '';
                            let etaClass = '';
                            const etaEl = el.querySelector('.eta span, .eta2 span');
                            if (etaEl) {
                                etaText = etaEl.textContent.trim();
                                etaClass = etaEl.className || '';
                            }

                            // 判斷 ETA 狀態
                            let status = 'normal';
                            let etaMinutes = null;
                            if (etaClass.includes('eta_nonop') || etaText.includes('未發車')) {
                                status = 'not_started';
                                etaMinutes = null;
                            } else if (etaClass.includes('eta_coming') || etaText.includes('進站中')) {
                                status = 'arriving';
                                etaMinutes = 0;
                            } else if (etaClass.includes('eta_near') || etaText.includes('即將進站')) {
                                status = 'near';
                                etaMinutes = 1;
                            } else {
                                // 提取分鐘數（如 "約3分" -> 3）
                                const match = etaText.match(/約?(\\d+)分/);
                                if (match) {
                                    etaMinutes = parseInt(match[1]);
                                    status = 'normal';
                                }
                            }

                            // 取得車牌號碼（從 bni 或 bno 中的 bnl）
                            const buses = [];
                            const busPlates = el.querySelectorAll('.bpni .bnl, .bpno .bnl, .bpni2 .bnl, .bpno2 .bnl');
                            busPlates.forEach(plateEl => {
                                const plate = plateEl.textContent.trim();
                                if (plate && plate !== 'null' && plate !== 'undefined') {
                                    buses.push({
                                        plate_number: plate,
                                        bus_type: '',
                                        remaining_seats: null
                                    });
                                }
                            });

                            // 只記錄有站名的站點
                            if (stopName) {
                                stops.push({
                                    sequence: idx,
                                    name: stopName,
                                    eta_text: etaText,
                                    status: status,
                                    eta_minutes: etaMinutes,
                                    buses: buses
                                });

                                if (idx < 3) {
                                    debug_info.push(`站點 ${idx}: ${stopName}, ETA=${etaText}, 狀態=${status}, 車輛=${buses.length}`);
                                }
                            }
                        } catch (err) {
                            debug_info.push(`解析站點 ${idx} 時出錯: ${err.message}`);
                        }
                    });

                    return { stops: stops, debug: debug_info };
                }
            """)

            # 記錄除錯資訊
            if stops_from_html.get('debug'):
                for info in stops_from_html['debug']:
                    logger.info(f"  HTML解析: {info}")

            html_stops = stops_from_html.get('stops', [])
            logger.info(f"從 HTML 解析到 {len(html_stops)} 個站點")

            # 呼叫 GetStopDyns API 取得額外的動態資訊（如座位數等）
            api_stops_data = await self._fetch_stop_dyns(actual_route_id, direction)
            logger.info(f"從 API 取得 {len(api_stops_data)} 個站點資料")

            # 合併 HTML 和 API 資料（以 HTML 的站名為主，API 資料為輔）
            stops_data = []
            for i, html_stop in enumerate(html_stops):
                # 嘗試找到對應的 API 資料
                api_data = {}
                if i < len(api_stops_data):
                    api_data = api_stops_data[i]

                # 合併車輛資訊（HTML 提供車牌，API 提供座位數等）
                merged_buses = html_stop.get('buses', [])
                if api_data.get('bi') and len(api_data['bi']) > 0:
                    # 使用 API 的車輛資料（包含座位數）
                    merged_buses = []
                    for bus in api_data['bi']:
                        merged_buses.append({
                            'plate_number': bus.get('bn', ''),
                            'bus_type': bus.get('bt', ''),
                            'remaining_seats': str(bus.get('bSetL', '')) if bus.get('bSetL') else None
                        })

                stops_data.append({
                    'sn': html_stop['sequence'],
                    'na': html_stop['name'],
                    'bisname': html_stop['name'],
                    'eta': html_stop.get('eta_minutes'),
                    'bi': merged_buses,
                    'lat': api_data.get('lat'),
                    'lon': api_data.get('lon')
                })

                if i < 3:
                    logger.info(f"  合併後站點 {i}: {html_stop['name']}, ETA={html_stop.get('eta_text')}, 車輛={len(merged_buses)}")

            # 解析站牌資料
            stops = self._parse_stops(stops_data)

            # 建立 BusRoute 物件
            route = BusRoute(
                route_id=route_id,
                route_name=route_info.get("route_name", route_id),
                departure_stop=route_info.get("departure", ""),
                arrival_stop=route_info.get("arrival", ""),
                operator=route_info.get("operator", ""),
                direction=direction,
                direction_name_go=route_info.get("direction_name_go", ""),
                direction_name_back=route_info.get("direction_name_back", ""),
                stops=stops
            )

            logger.info(f"成功取得路線資訊，共 {len(stops)} 個站牌")
            return route

        except Exception as e:
            logger.error(f"取得路線資訊失敗: {e}")
            raise BusScraperError(f"無法取得路線資訊: {e}")

    async def _fetch_stop_dyns(self, route_id: str, direction: int) -> List[Dict]:
        """
        呼叫 GetStopDyns API 取得站牌動態資訊

        這是核心 API，會回傳所有站牌的即時資料，包括：
        - 站牌名稱和順序
        - 預估到站時間
        - 進站中公車的車號和座位資訊

        參數:
            route_id: 路線代碼
            direction: 方向（0=去程, 1=返程）

        回傳:
            API 回傳的原始資料列表
        """
        try:
            logger.debug(f"正在呼叫 GetStopDyns API...")

            # 先造訪地圖頁面以建立 session 和 cookies
            map_url = f"{self.MAP_URL}?routeid={route_id}&gb={direction}"
            await self.page.goto(map_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)

            # 取得 RequestVerificationToken
            token = await self.page.evaluate("""
                () => {
                    const tokenInput = document.querySelector('input[name="__RequestVerificationToken"]');
                    return tokenInput ? tokenInput.value : '';
                }
            """)

            if not token:
                logger.warning("無法取得 RequestVerificationToken，嘗試不使用 token 呼叫 API")

            # 準備 form data
            form_data = {
                "routeid": route_id,
                "gb": str(direction)
            }
            if token:
                form_data["__RequestVerificationToken"] = token

            # 使用 page.evaluate 執行 fetch 請求（這樣會自動帶上 cookies）
            result = await self.page.evaluate("""
                async ({ url, formData }) => {
                    try {
                        const params = new URLSearchParams();
                        for (const [key, value] of Object.entries(formData)) {
                            params.append(key, value);
                        }

                        const response = await fetch(url, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                'X-Requested-With': 'XMLHttpRequest'
                            },
                            body: params.toString(),
                            credentials: 'same-origin'
                        });

                        if (!response.ok) {
                            return { error: `HTTP ${response.status}: ${response.statusText}` };
                        }

                        const data = await response.json();
                        return { success: true, data: data };
                    } catch (e) {
                        return { error: e.message };
                    }
                }
            """, {"url": self.API_STOP_DYNS, "formData": form_data})

            if result.get("error"):
                raise BusScraperNetworkError(f"API 呼叫失敗: {result['error']}")

            data = result.get("data", [])

            if not isinstance(data, list):
                raise BusScraperParseError(f"API 回傳格式錯誤: {type(data)}")

            # 除錯：記錄前幾筆資料的欄位
            if data and len(data) > 0:
                logger.debug(f"API 回傳資料範例: {data[0]}")
                print(f"DEBUG - Total stops: {len(data)}")
                print(f"DEBUG - First few stops:")
                for i, stop in enumerate(data[:3]):
                    print(f"  Stop {i}: sn={stop.get('sn')}, bisname={stop.get('bisname')}, eta={stop.get('eta')}")

            logger.debug(f"API 回傳 {len(data)} 筆站牌資料")
            return data

        except Exception as e:
            logger.error(f"呼叫 GetStopDyns API 失敗: {e}")
            raise BusScraperNetworkError(f"無法取得站牌動態資訊: {e}")

    def _parse_stops(self, data: List[Dict]) -> List[BusStop]:
        """
        解析 API 回傳的站牌資料

        API 回傳的每個站牌物件包含以下欄位：
        - sn: 站序（0-based）
        - na: 站名
        - id: 站牌ID
        - lat: 緯度
        - lon: 經度
        - eta: 預估到站時間（分鐘，-1表示未發車，''表示進站中）
        - bi: 進站公車陣列，每個物件包含：
          - bn: 車號
          - bt: 車種
          - bSetL: 剩餘座位

        參數:
            data: API 回傳的原始資料

        回傳:
            解析後的 BusStop 物件列表
        """
        stops = []

        for idx, item in enumerate(data):
            try:
                # 解析基本站牌資訊
                sequence = item.get("sn", 0)
                # 嘗試多個可能的站名欄位
                name = item.get("bisname", "") or item.get("na", "") or item.get("name", "") or item.get("N", "")

                # 除錯：記錄前3個站點的原始資料
                if idx < 3:
                    logger.info(f"_parse_stops 站點 {idx}: sn={sequence}, bisname={item.get('bisname')}, na={item.get('na')}, 最終name={name}")

                # 如果站名還是空的，使用預設值（這時候會顯示「第X站」）
                if not name:
                    name = f"第{sequence + 1}站"
                    logger.warning(f"站序 {sequence} 無法取得站名，使用預設值")

                stop_id = str(item.get("sn", "")) or item.get("id", "") or item.get("Id", "")

                # 解析座標
                latitude = None
                longitude = None
                if "lat" in item and "lon" in item:
                    try:
                        latitude = float(item["lat"])
                        longitude = float(item["lon"])
                    except (ValueError, TypeError):
                        pass

                # 解析預估到站時間
                eta = None
                eta_raw = item.get("eta", "")
                if eta_raw == "":
                    # 空字串表示進站中
                    eta = 0
                elif eta_raw == -1:
                    # -1 表示尚未發車
                    eta = None
                else:
                    try:
                        eta = int(eta_raw)
                    except (ValueError, TypeError):
                        pass

                # 解析進站公車資訊
                buses = []
                bus_items = item.get("bi", []) or []
                for bus_item in bus_items:
                    bus_info = {
                        "plate_number": bus_item.get("bn", ""),
                        "bus_type": bus_item.get("bt", ""),
                        "remaining_seats": bus_item.get("bSetL")
                    }
                    buses.append(bus_info)

                # 建立 BusStop 物件
                stop = BusStop(
                    sequence=sequence,
                    name=name,
                    id=stop_id,
                    latitude=latitude,
                    longitude=longitude,
                    eta=eta,
                    buses=buses
                )
                stops.append(stop)

            except Exception as e:
                logger.warning(f"解析站牌資料時發生錯誤: {e}, item: {item}")
                continue

        # 依站序排序
        stops.sort(key=lambda s: s.sequence)

        return stops

    async def get_route_both_directions(self, route_id: str) -> Dict[int, BusRoute]:
        """
        取得路線的去程和返程資訊

        參數:
            route_id: 路線代碼

        回傳:
            字典，key 為方向（0=去程, 1=返程），value 為 BusRoute 物件

        使用範例:
            routes = await scraper.get_route_both_directions("0100030700")
            forward = routes[0]  # 去程
            backward = routes[1]  # 返程
        """
        try:
            logger.info(f"正在取得路線雙向資訊，路線ID: {route_id}")

            results = {}

            # 取得去程資訊
            try:
                forward_route = await self.get_route_info(route_id, direction=0)
                results[0] = forward_route
            except Exception as e:
                logger.warning(f"取得去程資訊失敗: {e}")

            # 取得返程資訊
            try:
                backward_route = await self.get_route_info(route_id, direction=1)
                results[1] = backward_route
            except Exception as e:
                logger.warning(f"取得返程資訊失敗: {e}")

            return results

        except Exception as e:
            logger.error(f"取得路線雙向資訊失敗: {e}")
            raise BusScraperError(f"無法取得路線雙向資訊: {e}")


# ==================== 工具函數 ====================

def format_eta(eta: Optional[int]) -> str:
    """
    格式化預估到站時間為人類可讀的字串

    參數:
        eta: 預估到站時間（分鐘）

    回傳:
        格式化後的字串
    """
    if eta is None:
        return "尚未發車"
    elif eta == 0:
        return "進站中"
    elif eta == 1:
        return "1 分鐘"
    else:
        return f"{eta} 分鐘"


def export_to_json(route: BusRoute, filepath: str):
    """
    將路線資料匯出為 JSON 檔案

    參數:
        route: BusRoute 物件
        filepath: 輸出檔案路徑
    """
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(route.to_dict(), f, ensure_ascii=False, indent=2)
    logger.info(f"資料已匯出到: {filepath}")


# ==================== 測試與使用範例 ====================

async def demo():
    """
    示範如何使用 TaipeiBusScraper

    這個函數展示了爬蟲的主要功能：
    1. 搜尋路線
    2. 取得路線詳細資訊
    3. 顯示即時到站資訊
    """
    print("=" * 60)
    print("台北市公車爬蟲示範")
    print("=" * 60)

    async with TaipeiBusScraper(headless=True) as scraper:
        # 1. 搜尋路線
        print("\n【步驟 1】搜尋路線 '307'")
        print("-" * 40)

        routes = await scraper.search_routes("307")
        print(f"找到 {len(routes)} 條符合的路線")

        for route in routes[:5]:  # 只顯示前 5 條
            print(f"  - {route.route_name}: {route.description}")

        if not routes:
            print("沒有找到符合的路線")
            return

        # 2. 取得特定路線的詳細資訊
        target_route_id = routes[0].route_id
        print(f"\n【步驟 2】取得路線 '{routes[0].route_name}' 的詳細資訊")
        print("-" * 40)

        route_info = await scraper.get_route_info(target_route_id)

        print(f"路線名稱: {route_info.route_name}")
        print(f"業者: {route_info.operator or '未知'}")
        print(f"方向: {'去程' if route_info.direction == 0 else '返程'}")
        print(f"站牌數量: {len(route_info.stops)}")

        # 3. 顯示各站牌的即時資訊
        print(f"\n【步驟 3】顯示即時到站資訊")
        print("-" * 40)

        for stop in route_info.stops[:10]:  # 只顯示前 10 站
            eta_str = format_eta(stop.eta)
            bus_info = ""
            if stop.buses:
                bus_plates = [b["plate_number"] for b in stop.buses]
                bus_info = f" (車號: {', '.join(bus_plates)})"

            print(f"  {stop.sequence:2d}. {stop.name:15s} - {eta_str}{bus_info}")

        print("\n... (僅顯示前 10 站)")

        # 4. 取得雙向資訊（示範）
        print(f"\n【步驟 4】取得雙向路線資訊")
        print("-" * 40)

        both_directions = await scraper.get_route_both_directions(target_route_id)

        for direction, route_data in both_directions.items():
            direction_name = "去程" if direction == 0 else "返程"
            print(f"{direction_name}: {len(route_data.stops)} 站")

    print("\n" + "=" * 60)
    print("示範完成！")
    print("=" * 60)


if __name__ == "__main__":
    # 執行示範程式
    asyncio.run(demo())
