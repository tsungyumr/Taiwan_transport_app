import asyncio
import json
from bus_tdx_service import get_bus_service

async def test():
    service = get_bus_service()

    # 取得藍15的站點資料
    route_stops = await service.get_route_stops('藍15', 'NewTaipei', 0)
    print(f'取得 {len(route_stops)} 筆路線站點資料')

    # 取得站點位置
    all_uids = []
    for rs in route_stops:
        if rs.get('Direction', 0) != 0:
            continue
        for stop in rs.get('Stops', []):
            uid = stop.get('StopUID', '')
            if uid:
                all_uids.append(uid)

    print(f'收集到 {len(all_uids)} 個站點 UID')

    positions = await service.get_stop_positions_batch(all_uids)
    print(f'取得 {len(positions)} 個站點位置')

    # 顯示前3個站點的詳細資訊
    print('\n前3個站點位置:')
    for i, uid in enumerate(all_uids[:3]):
        pos = positions.get(uid, {})
        print(f'  {uid}: {pos}')

if __name__ == '__main__':
    asyncio.run(test())
