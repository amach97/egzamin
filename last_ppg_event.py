import arcpy
from math import sqrt, pi, atan
import pandas as pd

arcpy.env.overwriteOutput=1
arcpy.env.workspace= r'C:\Users\48691\Desktop\ppg\egzamin\dane'

bud = arcpy.CopyFeatures_management('BUBD.shp', arcpy.Geometry())               #poligony
bud_f = r'BUBD.shp'

bud_p = arcpy.FeatureVerticesToPoints_management("BUBD.shp", "BUBD_p.shp")      #punkty
bud_p_g = arcpy.CopyFeatures_management('BUBD_p.shp', arcpy.Geometry())

bud_line = arcpy.PolygonToLine_management("BUBD.shp", "BUBD_line.shp")          #linie
bud_line_g = arcpy.CopyFeatures_management('BUBD_line.shp', arcpy.Geometry())

FID=[]
x=[]
y=[]
curs = arcpy.da.SearchCursor(bud_p, ["OID@", "SHAPE@X", "SHAPE@Y"])
for line in curs:
    FID.append(line[0])
    x.append(line[1])
    y.append(line[2])

#1. Dlugosc
def segment_length_b(i):        #przed
    if i==0:
        j=len(x)-1
    else:
        j = i-1
    dl = round(sqrt((x[i]-x[j])**2+(y[i]-y[j])**2), 2)
    return dl

def segment_length_a(i):        #po
    if i==len(x)-1:
        j=0
    else:
        j=i+1
    dl = round(sqrt((x[i]-x[j])**2+(y[i]-y[j])**2), 2)
    return dl

#2. Kat
def Az(i,j):
    dx = x[j] - x[i]
    dy = y[j] - y[i]
    if dx==0 and dy>0:
        Az = 100
    elif dx==0 and dy<0:
        Az = 300
    elif dy==0 and dx>0:
        Az = 0
    elif dy==0 and dx<0:
        Az = 200
    elif dx==0 and dy==0:
        Az = 0
    else:
        A = (atan(abs(dy/dx)))*200/pi
        if dx>0 and dy>0:
            Az = A
        elif dx>0 and dy<0:
            Az = 200 - A
        elif dx<0 and dy<0:
            Az = 200 + A
        else:
            Az = 400 - A
    return round(Az, 4)

def vertex_angle(i):
    if i==0:
        j=i+1
        k=len(x)-1
    elif i==len(x)-1:
        j=0
        k=i-1
    else:
        j=i+1
        k=i-1
    if Az(i,j)>Az(i,k):
        kat = Az(i,j) - Az(i,k)
    else:
        kat = Az(i,k) - Az(i,k)
    return kat

#3. is node
gmlid=[]
desc = arcpy.SearchCursor(bud_p)
for line in desc:
    gmlid.append(line.gmlId)

def is_node(i):
    il = 0
    for j in range(len(x)):
        if x[i] == x[j] and y[i] == y[j] and gmlid[i] <> gmlid[j]:
            il = il + 1
    if il == 1:
        return 'Wierzcholek jest wezlem sasiedztwa z 1 elementem'
    if il > 1:
        return 'Wierzcholek jest wezlem sasiedztwa z {} elementami'.format(il)
    else:
        print 'Wierzcholek nie jest wezlem sasiedztwa'

#4. deflection
def deflection(met):
    mbg=arcpy.MinimumBoundingGeometry_management('BUBD.shp', "deflect{}.shp".format(met), met)
    linie = arcpy.PolygonToLine_management(mbg, "linie_{}.shp".format(met))
    odl = arcpy.Near_analysis(bud_p, linie)
    curs2 = arcpy.da.SearchCursor(bud_p,["NEAR_DIST"])
    distance=[]
    for row in curs2:
        dist = round(row[0],2)
        distance.append(dist)
    return distance

#5. intersect
def intersect(geom1, geom1g, geom2, geom2g, id1, id2):
    desc = arcpy.Describe(geom1)
    desc2 = arcpy.Describe(geom2)
    test1 = geom1g[id1].contains(geom2g[id2])
    test2 = geom1g[id1].crosses(geom2g[id2])
    test3 = geom1g[id1].disjoint(geom2g[id2])
    test4 = geom1g[id1].equals(geom2g[id2])
    test5 = geom1g[id1].overlaps(geom2g[id2])
    test6 = geom1g[id1].touches(geom2g[id2])
    test7 = geom1g[id1].within(geom2g[id2])
    print '{} id:{} and {} id:{} '.format(desc.shapeType, id1, desc2.shapeType, id2)
    print '     Contains = ', test1
    print '     Crosses = ', test2
    print '     Disjoint = ', test3
    print '     Equals = ', test4
    print '     Overlaps = ', test5
    print '     Touches = ', test6
    print '     Within = ', test7

#intersect(bud_f, bud, bud_p, bud_p_g, 2309, 26058)

#6. minimal geometry
def minimal_geometry(budynki):
    mbg_rec_ar = arcpy.MinimumBoundingGeometry_management(budynki, "mbg_{}.shp".format("RECTANGLE_BY_AREA"), "RECTANGLE_BY_AREA")
    mbg_rec_wd = arcpy.MinimumBoundingGeometry_management(budynki, "mbg_{}.shp".format("RECTANGLE_BY_WIDTH"), "RECTANGLE_BY_WIDTH")
    mbg_con_h = arcpy.MinimumBoundingGeometry_management(budynki, "mbg_{}.shp".format("CONVEX_HULL"), "CONVEX_HULL")
    mbg_cir = arcpy.MinimumBoundingGeometry_management(budynki, "mbg_{}.shp".format("CIRCLE"), "CIRCLE")
    min_geo= [mbg_rec_ar, mbg_rec_wd, mbg_con_h, mbg_cir]
    return min_geo

#zadanie egzaminacyjne
rec_ar = deflection("RECTANGLE_BY_AREA")
rec_wd = deflection("RECTANGLE_BY_WIDTH")
con_h = deflection("CONVEX_HULL")
cir = deflection("CIRCLE")
enve = deflection("ENVELOPE")

list = []
for i in range(len(x)-1):
    dl_przed = segment_length_b(i)
    dl_po = segment_length_a(i)
    angle_in = vertex_angle(i)
    l = [str(gmlid[i]), FID[i], dl_przed, dl_po, angle_in, rec_ar[i], rec_wd[i], con_h[i], cir[i], enve[i]]
    list.append(l)

df = pd.DataFrame(list, columns = ['gmlId', 'FID', 'LENGTH IN [m]', 'LENGTH OUT [m]', 'ANGLE IN [g]', 'RECTANGLE BY AREA [m]',
                                   'RECTANGLE_BY_WIDTH [m]', 'CONVEX HULL [m]', 'CIRCLE [m]', 'ENVELOPE [m]'])

df.to_csv('results.csv', index=False, header=True, sep=';')