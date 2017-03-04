#!/usr/bin/env python3

from sys import argv
if len(argv)<2:
    print("Give .we file as argument.")
    exit(1)
infilename = argv[1]
if len(argv) ==3:
    outfilename = argv[2]
else:
    outfilename=infilename+".vox"

with open(infilename,'r') as f:
    s=f.read()
s=s[9:]
ss=s.replace("=",":").replace("[",'').replace("]",'').replace("{}",'0').strip()[1:-1]
nodes = {}
for node in eval(ss):
    nodes[(node['x'],node['y'],node['z'],)]=node['name']

#print( nodes)

maxx=maxz=maxy=-9999999999
for (x,y,z), node in nodes.items():
    maxx=max(x,maxx)
    maxy=max(y,maxy)
    maxz=max(z,maxz)

#print(maxx, maxy, maxz)

types = set()
for x,y,z in ((x,y,z) for x in range(maxx+1) for y in range(maxy+1) for z in range(maxz+1)):
    if (x,y,z) in nodes:
        node=nodes[(x,y,z)]
        types.add(node)

types=sorted(list(types))
#print(types, len(types))

if len(types)> 256:
    print("No luck: too many different nodes for .vox palette (256 colors max).")
    exit(1)


with open('colors.txt','r') as f:
    c=f.read()
colors={}
for name, r,g,b in [l.split()[:4] for l in c.split('\n') if not '_' in l and ':' in l]:
    colors[name]=(int(r),int(g),int(b))

#print(colors)

import struct
totalbytes = 0
def byteint(i):
    return struct.pack('<i', i)

def chunk(name, data):
    ch = bytearray(name)
    ch+= byteint(len(data))
    ch+= byteint(0) #child size
    ch+= data
    return ch

#SIZE
sizebytes=bytearray()
sizebytes+=byteint(maxx)+byteint(maxz)+byteint(maxy)

#RGBA
rgbabytes=bytearray()
palette ={}
counter = 0
for ty in types:
    r,g,b = (80,80,80)
    if ty in colors:
        r,g,b = colors[ty]
    palette[ty] = counter
    rgbabytes+=struct.pack('BBBB', r, g, b, 80)
    counter +=1

#XYZI
xyzibytes=bytearray()
voxelcount=0
for (x,y,z), node in nodes.items():
    xyzibytes += struct.pack('BBBB', x,z,y ,palette[node])
    voxelcount +=1
xyzibytes = byteint(voxelcount) + xyzibytes

#PACK
#packbytes = bytearray(b'PACK')+byteint(1)

stream = bytearray()
stream += chunk(b'SIZE', sizebytes)
stream += chunk(b'XYZI', xyzibytes)
stream += chunk(b'RGBA', rgbabytes)
totalbytes = len(stream)

mainchunk = bytearray(b'VOX ')
mainchunk+=byteint(150) 
mainchunk+=bytearray(b'MAIN')
mainchunk+=byteint(0)+byteint(totalbytes)

stream = mainchunk + stream

with open(outfilename, 'wb') as of:
    of.write( stream)
