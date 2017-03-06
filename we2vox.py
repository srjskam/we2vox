#!/usr/bin/env python3

#https://github.com/ephtracy/voxel-model/blob/master/MagicaVoxel-file-format-vox.txt

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
if s[0] not in "45":
    print("Warning, newer version of .we ("+s[0]+", supported: 4, 5")
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
for name, r,g,b in [l.split()[:4] for l in c.split('\n') if  ':' in l]:
    colors[name]=(int(r),int(g),int(b))

#print(colors)

import struct
totalbytes = 0
def byteint(i):
    return struct.pack('<i', i)

def chunk(name, content=b'', children=b''):
    ch = bytearray(name)
    ch+= byteint(len(content))
    ch+= byteint(len(children))
    ch+= content
    ch+= children
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
    else:
        print("Color for "+ty+" undefined.")
    palette[ty] = counter
    rgbabytes+=struct.pack('BBBB', r, g, b, 0xff)
    counter +=1
while counter < 256:
    rgbabytes+=struct.pack('BBBB', counter,counter,counter, 0xff)
    counter += 1
    

#MATT
mattbytes=bytearray()
metals = ['steel','iron','brass','gold','zinc','copper','tin','bronze','silver','chromium','titanium']
emitters = ['lamp','light','glow','torch','chandelier','sconce']
mattchunks = bytearray()
for name, num in palette.items():
    if "glass" in name or "water" in name:
        mattbytes = bytearray()
        mattbytes += byteint(num)
        mattbytes += byteint(2) #glass
        mattbytes += struct.pack('<f', 0.8)
        mattbytes += byteint( 1<<1 #rough
                            | 1<<3 #IOR
                            | 1<<4 #atten
                            )
        mattbytes += struct.pack('<f', 0.3)
        mattbytes += struct.pack('<f', 0.3)
        mattbytes += struct.pack('<f', 0.1)
        mattchunks += chunk(b'MATT', mattbytes)
    elif any(metal in name for metal in metals):
        mattbytes = bytearray()
        mattbytes += byteint(num)
        mattbytes += byteint(1) #metal
        mattbytes += struct.pack('<f', 0.8)
        mattbytes += byteint( 1<<1 #rough
                            | 1<<2 #specular
                            )
        mattbytes += struct.pack('<f', 0.3)
        mattbytes += struct.pack('<f', 0.8)
        mattchunks += chunk(b'MATT', mattbytes)
    elif any(emitter in name for emitter in emitters):
        mattbytes = bytearray()
        mattbytes += byteint(num)
        mattbytes += byteint(3) #emitter
        mattbytes += struct.pack('<f', 1.0)
        mattbytes += byteint( 1<<5 #power
                            | 1<<6 #glow
                            )
        mattbytes += struct.pack('<f', 0.9)
        mattbytes += struct.pack('<f', 0.9)
        mattchunks += chunk(b'MATT', mattbytes)

#XYZI
xyzibytes=bytearray()
voxelcount=0
for (x,y,z), node in nodes.items():
    xyzibytes += struct.pack('BBBB', x,z,y ,palette[node])
    voxelcount +=1
xyzibytes = byteint(voxelcount) + xyzibytes

#PACK
#packbytes = bytearray(b'PACK')+byteint(1)

stream = bytearray(b'VOX ')
stream+=byteint(150) 
stream+=chunk( b'MAIN' , children 
                    = chunk( b'SIZE' , content=sizebytes)
                    + chunk( b'XYZI' , content=xyzibytes)
                    + chunk( b'RGBA' , content=rgbabytes)
                    + mattchunks
             )

with open(outfilename, 'wb') as of:
    of.write( stream)
