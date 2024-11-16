import requests
import time
import json

stats_cache = {}
scale_all_cache = {}

def get_sanhounan_stats(name):
    global stats_cache
    if name in stats_cache:
        print('read from cache')
        return stats_cache[name]
    url = 'https://nodocchi.moe/api/phoenix_status.php'
    resp = requests.get(url, {'all': 1, 'username': name}).text
    resp_json = json.loads(resp)
    stats_cache[name] = resp_json['s3']
    return resp_json['s3']

def get_sanhounan_scale_all():
    global scale_all_cache
    if len(scale_all_cache) > 0:
        print('read scale_all from cache')
        return scale_all_cache
    url = 'https://nodocchi.moe/s/phoenix_scale_all.js'
    resp = requests.get(url).text
    resp_json = json.loads(resp)
    scale_all_cache = resp_json['s3']
    return resp_json['s3']

def get_interested_stats(full_stats):
    interested_stats = {
        'n_game': full_stats['totalrecord'],
        '1st_rate': full_stats['order_top_Z'],
        '2nd_rate': 1 - full_stats['order_top_Z'] - full_stats['order_last_Z'],
        '3rd_rate': full_stats['order_last_Z'],
        'stable_dan': full_stats['stablerank_phoenix_X'],
        'agari_rate': full_stats['agariC'],
        'agari_daten': full_stats['agariVT'],
        'houjuu_rate': full_stats['houjuuC'],
        'riichi_rate': full_stats['riichC'],
        'fuuro_rate': full_stats['fuuroC'],
        'fuuro_daten': full_stats['agariVFT'],
        'agari_dama_rate': full_stats['damaV'],
        'some_rate': full_stats['someV'],
        }
    return interested_stats

def get_interested_scales(full_scall_all):
    interested_scales = {
        'agari_dama_rate': full_scall_all['damaV']['data'],
        'some_rate': full_scall_all['someV']['data'],
    }
    return interested_scales

def get_interested_percentiles(interested_stats, interested_scales):
    interested_percentiles = {}
    for scale in interested_scales:
        if scale in interested_stats:
            for i in range(1, 100):
                if float(interested_scales[scale][i]) > interested_stats[scale]:
                    interested_percentiles[scale] = i - 1
                    break
            else:
                interested_percentiles = 99
    return interested_percentiles

main_perspective_name = '你的天凤昵称'

def get_wg_from_nodocchi():
    url = 'https://nodocchi.moe/s/wg.js'
    resp = requests.get(url).text
    resp_json = json.loads(resp)
    return resp_json

def get_players_and_id(wg_json, main_perspective_name):
    most_recent_starttime = 0
    found = None
    id = ''
    for table in wg_json:
        if table['info']['playernum'] == 3:
            players = [table['players'][0]['name'], table['players'][1]['name'], table['players'][2]['name']]
            if main_perspective_name in players:
                starttime = table['info']['starttime']
                if starttime > most_recent_starttime:
                    most_recent_starttime = starttime
                    found = players
                    id = table['info']['id']
    return found, id

current_id = ''
def cronjob():
    file_content = ''
    try:
        wg_json = get_wg_from_nodocchi()
        players, id = get_players_and_id(wg_json, main_perspective_name)
        if players == None:
            print('not found')
            return
        global current_id
        my_seat = 0
        if id != current_id:
            for i in range(3):
                player = players[i]
                if player == main_perspective_name:
                    my_seat = i
            for i in range(2, -1, -1):
                player = players[i]
                if player != main_perspective_name:
                    print(player)
                    interested_stats = get_interested_stats(get_sanhounan_stats(player))
                    interested_scales = get_interested_scales(get_sanhounan_scale_all())
                    interested_percentiles = get_interested_percentiles(interested_stats, interested_scales)
                    print(interested_stats, interested_percentiles)
                    file_content += ['自家', '下家', '对家', '上家'][(i + 4 - my_seat) % 4] + ' ' + player
                    file_content += '\n'
                    file_content += f"{interested_stats['n_game']}战 安{round(interested_stats['stable_dan'], 2):.2f}"
                    file_content += '\n'
                    file_content += f"和了率 {round(interested_stats['agari_rate'], 3):.3f}"
                    file_content += '\n'
                    file_content += f"放铳率 {round(interested_stats['houjuu_rate'], 3):.3f}"
                    file_content += '\n'
                    file_content += f"副露率 {round(interested_stats['fuuro_rate'], 3):.3f}"
                    file_content += '\n'
                    file_content += f"立直率 {round(interested_stats['riichi_rate'], 3):.3f}"
                    file_content += '\n'
                    file_content += f"和了点 {int(round(interested_stats['agari_daten'], 0))}"
                    file_content += '\n'
                    file_content += f"副露点 {int(round(interested_stats['fuuro_daten'], 0))}"
                    file_content += '\n'
                    file_content += f"默听率 {round(interested_stats['agari_dama_rate'], 3):.3f} {interested_percentiles['agari_dama_rate']}%位"
                    file_content += '\n'
                    file_content += f"染手率 {round(interested_stats['some_rate'], 3):.3f} {interested_percentiles['some_rate']}%位"
                    file_content += '\n\n'
            with open('stats.txt', 'w') as f:
                f.write(file_content)
            current_id = id
    except Exception as e:
        print('error', e)
while True:
    cronjob()
    time.sleep(15)
