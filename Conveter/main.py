# -*- coding: utf-8 -*-
###個別に設定する変数START
##ファイル入出力設定
input_path = "./BP000_CSV/" #インプットするCSVファイルのディレクトリ
filename_end = 'm.csv' #インプットするCSVファイル名の末尾（※BP〇〇〇_△△△△△m.csv（例：BP001_00060m.csv）という形式のファイル名を想定しています。）
output_file = './output.czml' #アウトプットするCZMLファイルのファイル名
GSI_GEOID_FILE_NAME = 'gsigeo2011_ver2_2.asc' #ジオイドモデルのファイル名

#読み込むファイルの開始時刻および終了時刻（※ファイル名の△△△△△mをベースとした分での指定）
start_time = 0 #開始時刻
stop_time = 1440 #終了時刻

##CZML開始の時刻（UTC）
year_t = 2025 #年
mon_t = 3 #月
day_t = 21 #日
hour_t = 0 #時
min_t = 0 #分

#浸水の色分け（[R,G,B,A]）
flood_color = [100, 160, 190, 230]

# CSVの列名の辞書（左側を読み込むCSVの属性名に変更してください。右側は変更しないでください。)
rename_mapping = {
    'メッシュコード': 'MESH',
    '標高': 'dem',
    '浸水深': 'flood_depth',
    '流速': 'flow_velocity',
    'P1緯度': 'P1_lat',
    'P1経度': 'P1_lon',
    'P2緯度': 'P2_lat',
    'P2経度': 'P2_lon',
    'P3緯度': 'P3_lat',
    'P3経度': 'P3_lon',
    'P4緯度': 'P4_lat',
    'P4経度': 'P4_lon'
}

###個別に設定する変数END

import json
import os
import pandas as pd
import csv
import math
import importlib
import geopandas as gpd
from shapely.geometry import Polygon
from datetime import datetime, timedelta

#ジオイドデータはglobalで使う
global geoid
global geoidparam
global glamn
global glomn
global dgla
global dglo
global nla
global nlo

#ジオイドデータを読込みます。事前作成したデータファイルモジュール（geoidData.py）が存在しない時は
#国土地理院のジオイドデータファイルから作成します。（次回以降の処理が若干早くなる）
def getGeoidData():
    global geoid
    global glamn
    global glomn
    global dgla
    global dglo
    global nla
    global nlo
    if (os.path.exists(os.path.join(os.getcwd(),'geoidData.py')) == False):
        print('国土地理院のジオイドファイルからデータファイルを作成します(初回のみ)')
        if (os.path.exists(os.path.join(os.getcwd(),GSI_GEOID_FILE_NAME)) == False):
            print('エラー:データファイルがありません')
            print('同じフォルダに国土地理院のジオイドファイル「' + GSI_GEOID_FILE_NAME + '」を置いてください')
            return False
        createGeoidData()
    else:
        print('データファイルを読込中')
        module = importlib.import_module('geoidData')
        geoid = module.setGeoid()
        misc = module.setMiscData()
        glamn = misc["glamn"]
        glomn = misc["glomn"]
        dgla = misc["dgla"]
        dglo = misc["dglo"]
        nla = misc["nla"]
        nlo = misc["nlo"]
    #ヘッダのdglaの有効桁数違いで地理院プログラムと微小な差異があったので、より計算値に近づける
    dgla = math.floor(dgla * (nla - 1)) / (nla - 1)
    dglo = math.floor(dglo * (nlo - 1)) / (nlo - 1)

#国土地理院のジオイドデータからPythonのデータを書きだして、次回から使えるようにします。
def createGeoidData():
    global geoid
    global glamn
    global glomn
    global dgla
    global dglo
    global nla
    global nlo
    f = open(os.path.join(os.getcwd(),GSI_GEOID_FILE_NAME), 'r')
    #f = open('gsigeo2011_ver2_1.asc', 'r')
    line = f.readline()
    #  20.00000 120.00000 0.016667 0.025000 1801 1201 1 ver2.1         
    linestr = '' + line
    linestr = linestr.strip() 
    header = linestr.split(" ")
    glamn = float(header[0])
    glomn = float(header[1])
    dgla = float(header[2])
    dglo = float(header[3])
    nla = int(header[4])
    nlo = int(header[5])

    geoid = {}
    la = 0
    lo = 0
    while line:
        line = f.readline()
        linestr = '' + line
        linestr = linestr.strip()
        g = linestr.split(" ")
        glen = len(g)
        for i in range(0, glen):
            if(g[i].strip() == ""):
                continue
            if(g[i]!='999.0000'):
                geoid[str(la) + "_" + str(lo)] = float(g[i])
            lo +=1
            if (lo == nlo):
                lo = 0
                la+=1
    
    f.close()

    fw = open('geoidData.py', 'w') # 書き込みモードで開く
    fw.writelines('def setGeoid():\n')
    #geoid = [[999] * 1201 for i in range(1801)]
    fw.writelines('\tgeoid = {}\n')
    for la in range(0, nla):
        for lo in range(0, nlo):
            if(str(la) + "_" + str(lo) in geoid.keys()):
                fw.writelines('\tgeoid["' + str(la) + '_' + str(lo) + '"] = ' + str(geoid[str(la) + "_" + str(lo)]) + '\n')
    fw.writelines('\treturn geoid\n')
    fw.writelines('def setMiscData():\n')
    fw.writelines('\tmisc = {}\n')
    fw.writelines('\tmisc["glamn"] = ' + str(glamn) + '\n')
    fw.writelines('\tmisc["glomn"] = ' + str(glomn) + '\n')
    fw.writelines('\tmisc["dgla"] = ' + str(dgla) + '\n')
    fw.writelines('\tmisc["dglo"] = ' + str(dglo) + '\n')
    fw.writelines('\tmisc["nla"] = ' + str(nla) + '\n')
    fw.writelines('\tmisc["nlo"] = ' + str(nlo) + '\n')
    fw.writelines('\treturn misc\n')

    fw.close()
    
#緯度経度からジオイド値を求める
def getGeoidValue(lon, lat):
    global geoid
    global glamn
    global glomn
    global dgla
    global dglo
    global nla
    global nlo
    #囲う矩形を求める
    j = int(math.floor((lon - glomn) / dglo))
    i = int(math.floor((lat - glamn) / dgla))
    if( i < 0 or i >= nla or j < 0 or j >= nlo):
        #print('エラー：緯度経度が範囲外です')
        return 999.00

    if ((not (str(i)+"_"+str(j) in geoid.keys())) or (not (str(i)+"_"+str(j+1) in geoid.keys())) or (not (str(i+1)+"_"+str(j) in geoid.keys())) or (not (str(i+1)+"_"+str(j+1) in geoid.keys()))):
        return 999.00
    wlon = glomn + j * dglo
    elon = glomn + (j+1) * dglo
    slat = glamn + i * dgla
    nlat = glamn + (i+1) * dgla

    t = (lat - slat) / (nlat - slat)
    u = (lon - wlon) / (elon - wlon)

    Z = (1 - t) * (1 - u) * geoid[str(i)+"_"+str(j)] + (1 - t) * u * geoid[str(i)+"_"+str(j+1)] + t * (1 - u) * geoid[str(i+1)+"_"+str(j)] + t * u * geoid[str(i+1)+"_"+str(j+1)]
    Z = Z * 100000
    Z = math.floor(Z + 0.5)
    Z = Z / 100000
    return Z

#CSVファイル中の高さ(楕円体高)カラムを標高値に置き換えて出力します
def convertCSV(infile, outfile):
    global geoid
    #header check
    f = open(infile, 'r')
    header = f.readline().lower()
    if((('latitude' in header) and ('longitude' in header) and ('altitude' in header)) or (('lat' in header) and (('long' in header) or ('lon' in header) or ('lng' in header)) and ('alt' in header))):
        startRow=1
    else:
        #read one more line
        header = f.readline()
        startRow=2
    header = header.strip()
    f.close()

    #区切り文字の推測
    delimChar = ''
    if(delimChar==''):
        headers = header.split(",")
        if(len(headers)>2):
            delimChar = ','
    if(delimChar==''):
        headers = header.split("\t")
        if(len(headers)>2):
            delimChar = '\t'
    if(delimChar==''):
        headers = header.split(" ")
        if(len(headers)>2):
            delimChar = ' '
    if(delimChar==''):
        print('区切り文字が不明です。処理できません。')

    #高さカラムの特定
    altCol = -1 #assume x,y,z
    for col in range(0, len(headers)):
        colstr = headers[col].lower().strip()
        if(colstr=='z'):
            altCol = col
        elif(colstr=='alt'):
            altCol = col
        elif(colstr=='altitude'):
            altCol = col
        elif(colstr=='z/altitude'):
            altCol = col
        elif(('altitude' in colstr) and ('z' in colstr)):
            altCol = col

    #緯度カラムの特定
    latCol = -1 #assume x,y,z
    for col in range(0, len(headers)):
        colstr = headers[col].lower().strip()
        if(colstr=='latitude'):
            latCol = col
        elif(colstr=='lat'):
            latCol = col
        elif(('latitude' in colstr) and ('y' in colstr)):
            latCol = col

    #経度カラムの特定
    lonCol = -1 #assume x,y,z
    for col in range(0, len(headers)):
        colstr = headers[col].lower().strip()
        if(colstr=='longitude'):
            lonCol = col
        elif(colstr=='lng'):
            lonCol = col
        elif(colstr=='lon'):
            lonCol = col
        elif(colstr=='long'):
            lonCol = col
        elif(('longitude' in colstr) and ('x' in colstr)):
            lonCol = col
    #カラムが特定できない時はエラー
    if(altCol==-1 or lonCol==-1 or latCol==-1):
        print('列が不明です。処理できません。')
        exit()

    #CSV処理
    hasInvalid = False
    with open(infile, 'r') as fin, open(outfile, 'w') as fout:
        #CSV Reader
        reader = csv.reader(fin, delimiter=delimChar)
        
        #ヘッダをそのままコピー
        for row in range(0,startRow):
            fout.writelines(delimChar.join(next(reader))+'\n')
        
        #各行の処理
        for row in reader:
            EllapsoidHeight = float(row[altCol])
            lat = float(row[latCol])
            lon = float(row[lonCol])
            geoidval = getGeoidValue(lat,lon)
            elevation = EllapsoidHeight - geoidval  #標高＝楕円体高-ジオイド高
            if(geoidval==999.00):
                #ジオイド値が正常に取得できない
                elevation = 999999
                hasInvalid = True 
            row[altCol] = "{0:.3f}".format(elevation)   #高さカラムを差し替え
            fout.writelines(delimChar.join(row)+'\n')   #出力
    if(hasInvalid):
        print('ジオイドの取得に失敗したデータがあります。確認ください。該当するデータは標高を 999999 にしています。')
    else:
        print('処理を正常に終了しました')

getGeoidData()
getGeoidData()

###初期値設定
dis_czmls = [
    {
     "id": "document",
     "name": "CZML",
     "version": "1.0"
     }
    ]
id_dczml = 0
now_timez = str(year_t).zfill(4)+"-"+str(mon_t).zfill(2)+"-"+str(day_t).zfill(2)+"T"+str(hour_t).zfill(2)+":"+str(min_t).zfill(2)+":00.000Z"
###初期値設定END


###読込ディレクトリ設定
files = os.listdir(input_path)
files.sort()
files = [i for i in files if i.endswith(filename_end) == True]
###読込ディレクトリ設定END

#CSVの読み込み上限変更
OVER_SIZE_LIMIT = 200_000_000
csv.field_size_limit(OVER_SIZE_LIMIT)

file_no = 0
for file in files:
    # CSVファイルのパス
    file_path = input_path + file
    #時系列以外のcsvファイルを除外する
    if file[len(file)-5:len(file)] == "m.csv":
        now_time = file[len(file)-10:len(file)-5]
        # 変換対象時間外の場合スキップする
        if int(now_time) < start_time or int(now_time) > stop_time:
            print('変換対象時間外のためスキップ:'+file)
        else :
            if len(files)-1 >= file_no+1 :
                #次のファイルのタイムスタンプを確認
                time_hen = int(files[file_no+1][len(files[file_no+1])-10:len(files[file_no+1])-5]) - int(now_time)
            before_timez = now_timez
            #次の時間の計算
            new_datetime = datetime(year_t, mon_t, day_t, hour_t, min_t, 0) + timedelta(minutes=time_hen)
            year_t = new_datetime.year
            mon_t = new_datetime.month
            day_t = new_datetime.day
            hour_t = new_datetime.hour
            min_t = new_datetime.minute
    
            now_timez = str(year_t).zfill(4)+"-"+str(mon_t).zfill(2)+"-"+str(day_t).zfill(2)+"T"+str(hour_t).zfill(2)+":"+str(min_t).zfill(2)+":00.000Z"
            time_zone = before_timez+"/"+now_timez
            file_no = file_no + 1
            # CSVファイルをNumPy配列として読み込む
            data = pd.read_csv(file_path, skiprows=2, encoding='shift-jis')
    
            # 列名を変更する
            data = data.rename(columns=rename_mapping)
            data = data[list(rename_mapping.values())]
    
            data['P1_lon'] = data['P1_lon'].round(12)
            data['P3_lon'] = data['P3_lon'].round(12)
            data['P1_lat'] = data['P1_lat'].round(11)
            data['P3_lat'] = data['P3_lat'].round(11)
            
            # 各行ごとにP1緯度とP3緯度の平均を計算し、新しい列に追加する
            data['mesh_lon'] = (data['P1_lon'] + data['P3_lon']) / 2
            
            # 各行ごとにP1経度とP3経度の平均を計算し、新しい列に追加する
            data['mesh_lat'] = (data['P1_lat'] + data['P3_lat']) / 2
                    
            # 各行ごとにP3経度とP1経度の差を計算し、新しい列に追加する
            data['dem+flood_depth'] = (data['dem'] + data['flood_depth']) 
            
            point_cloudP1 = data[['P1_lon', 'P1_lat', 'dem+flood_depth']].values.tolist()
            point_cloudP2 = data[['P3_lon', 'P1_lat', 'dem+flood_depth']].values.tolist()
            point_cloudP3 = data[['P3_lon', 'P3_lat', 'dem+flood_depth']].values.tolist()
            point_cloudP4 = data[['P1_lon', 'P3_lat', 'dem+flood_depth']].values.tolist()
            
            #全頂点の高さの平均を算出
            point_cloud = point_cloudP1 + point_cloudP2 + point_cloudP3 + point_cloudP4
            for point_i in range(len(point_cloud)):
                point_cloud[point_i][2] = getGeoidValue(point_cloud[point_i][0],point_cloud[point_i][1]) + point_cloud[point_i][2]
            df_point_cloud = pd.DataFrame(point_cloud, columns=['x', 'y', 'z'])
            df_npts = df_point_cloud.groupby(['x', 'y'], as_index=False).agg({'z': 'mean'})
    
            triT41 = data[['mesh_lon', 'mesh_lat', 'P1_lon', 'P3_lat', 'P1_lon', 'P1_lat', 'mesh_lon', 'mesh_lat']].values.tolist()        
            triT12 = data[['mesh_lon', 'mesh_lat', 'P3_lon', 'P1_lat', 'P1_lon', 'P1_lat', 'mesh_lon', 'mesh_lat']].values.tolist()        
            triT23 = data[['mesh_lon', 'mesh_lat', 'P3_lon', 'P1_lat', 'P3_lon', 'P3_lat', 'mesh_lon', 'mesh_lat']].values.tolist()        
            triT34 = data[['mesh_lon', 'mesh_lat', 'P1_lon', 'P3_lat', 'P3_lon', 'P3_lat', 'mesh_lon', 'mesh_lat']].values.tolist()        
            
            geo_tri = triT41 + triT12 + triT23 + triT34        
            # 地形情報を格納するリスト 
            geo_poly = []
    
            for row in geo_tri :        
                coords = [(row[0], row[1]), (row[2], row[3]), (row[4], row[5]), (row[6], row[7])]
                geo_poly.append(Polygon(coords))
            
            #gpdでpolygon化
            polygons = gpd.GeoDataFrame({
                'geometry': geo_poly
                }, crs="EPSG:4326")
            #ディゾルブ処理の実行
            dissolved = polygons.dissolve()
                    
            # MultiPolygonから座標を抽出してリスト化
            coordinates_list = json.loads(dissolved.to_json())['features'][0]['geometry']['coordinates']
            
            # MultiPolygonから座標を抽出してDF化
            coordinates_diss = []
            for geoms in coordinates_list:
                coordinates_df = []
                for geom in geoms:
                    df = pd.DataFrame(geom, columns=['x', 'y'])
                    mdf = pd.merge(df, df_npts, on=['x', 'y'], how='inner')
                    coordinates_df.append(mdf.values)
                coordinates_diss.append(coordinates_df)
                    
    
            
            i = 0
            # DFから受け取った座標をもとにCZML化
            for tri_ins in coordinates_diss:
                i = 0
                tri_xyz3 = []
                hole_xyz3 = []
                holes_xyzs3 = []
                for tri_in in tri_ins:
                    if i == 0:            
                        tri_xyz3 = tri_in.flatten().tolist()
                        i = 1
                    elif i == 1 :
                        hole_xyz3 = tri_in.flatten().tolist()
                        i = i + 1
                            
                    else :
                        holes_xyzs3.append(tri_in.flatten().tolist())
                        i = i + 1
                        
                czml_load = {
                    "id": id_dczml,
                    "availability": time_zone,
                    "polygon": {
                        "positions": {
                            "cartographicDegrees": tri_xyz3
                            },
                        "holes": {
                            "cartographicDegrees": [hole_xyz3]
                            },
                        "material": {
                            "solidColor": {
                                "color": {
                                    "rgba": flood_color
                                    }
                                }
                            },
                        "perPositionHeight": "True"
                        }
                    }
                for xyzs in holes_xyzs3:
                    czml_load['polygon']['holes']['cartographicDegrees'].append(xyzs)
                dis_czmls.append(czml_load)
                id_dczml = id_dczml + 1
            print(file+" 処理完了")    
    
with open(output_file, 'w') as f:
    json.dump(dis_czmls, f, indent=2, ensure_ascii=False)

print('完了')


