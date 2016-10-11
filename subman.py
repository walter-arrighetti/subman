#!/usr/bin/python
##########################################################
#  subman 2.0                                            #
#                                                        #
#    TXT- and SCR-format subtitle editor for both 2D     #
#    and 3D (stereoscopic) subtitling. Checks both       #
#    existing subtitles' syntax and timeline conformity  #
#    and performs global/local subtitles' positioning    #
#    with respect to TimeCode, frame position and (for   #
#    stereo subtitles) depth.                            #
#                                                        #
#    Copyright (C) 2010 Walter Arrighetti, Phd           #
#    All Rights Reserved.                                #
##########################################################

import sys
import os
import re

VERSION = "2.0"
leadIn, leadOut, TC, padX, padY, padZ, fps, noZ, hasZ, set_Z = 0, 0, 0, 0, 0, None, 24, False, False, None

def frame2TC(frame, fps=24., drop=False, fulldispl=False, signed=False):
	fr = abs(frame)
	hours = mins = secs = rfr = 0
	hours = fr//(3600*fps)
	mins = fr//(60*fps) - 60*hours
	secs = fr/fps - 60*mins - 3600*hours
	rfr = fr%fps
	if not drop:	TC = ("%02d:%02d" % (mins,secs))
	else:	TC = ("%02d;%02d" % (mins,secs))
	if rfr>0 or fulldispl:
		if fps<100:	TC += (".%02d"%rfr)
		else:	TC += (".%d"%rfr)
	if hours>0 or fulldispl:
		if hours<10:
			if not drop:	TC = ("%02d:"%hours) + TC
			else:	TC = ("%02d;"%hours) + TC
		else:
			if not drop:	TC = ("%d:"%hours) + TC
			else:	TC = ("%d;"%hours) + TC
	if signed and frame<0:	return "-%s"%TC
	else:	return TC

def frame2subTC(frame, fps=24., drop=False, fulldispl=False, signed=False):
	fr = abs(frame)
	hours = mins = secs = rfr = 0
	hours = fr//(3600*fps)
	mins = fr//(60*fps) - 60*hours
	secs = fr/fps - 60*mins - 3600*hours
	rfr = fr%fps
	if not drop:	TC = ("%02d:%02d" % (mins,secs))
	else:	TC = ("%02d;%02d" % (mins,secs))
	if rfr>0 or fulldispl:
		if fps<100:	TC += (":%02d"%rfr)
		else:	TC += (":%d"%rfr)
	if hours>0 or fulldispl:
		if hours<10:
			if not drop:	TC = ("%02d:"%hours) + TC
			else:	TC = ("%02d;"%hours) + TC
		else:
			if not drop:	TC = ("%d:"%hours) + TC
			else:	TC = ("%d;"%hours) + TC
	if signed and frame<0:	return "-%s"%TC
	else:	return TC


def TC2frame(string, fps=24, signed=False):
	if signed and (string[0] in '+-'):
		time = re.match(r"((?P<hh>\d+):)?(?P<mm>\d{1,2}):(?P<ss>\d{1,2})(\.(?P<ff>\d{1,2}))?", string[1:])
	else:
		time = re.match(r"((?P<hh>\d+):)?(?P<mm>\d{1,2}):(?P<ss>\d{1,2})(\.(?P<ff>\d{1,2}))?", string)
	if time.group('hh')==None:	hh=0
	else:	hh=int(time.group('hh'))
	if time.group('mm')==None:	mm=0
	else:	mm=int(time.group('mm'))
	if time.group('ss')==None:	ss=0
	else:	ss=int(time.group('ss'))
	if time.group('ff')==None:	ff=0
	else:	ff=int(time.group('ff'))
	if signed and string[0]=='-':	return -(fps*(3600*hh+60*mm+ss)+ff)
	else:	return fps*(3600*hh+60*mm+ss)+ff

def syntax():
	print """Usage: subman file.ext [[leadIn]-[leadOut]] [+|-[hh:]mm:ss[.ff]] [Nfps|Hz]
               [x+|-offset] [y+|-offset] [z=|+|-offset] [--noz] [--txt|scr]

  Permforms substitutions/conversions of TXT & SCR subtitle files (timecode and
 /or position shitfs) and renames the new version with a prepending underscore.
  TXT files may have a header with each line beginning with '#'; following
 lines must hold *Tab-separated* values as follows:
     hh:mm:ss:ff    hh:mm:ss:ff    filename.ext    123    456    [12]
  SCR files must have *space-separated* values as follows:
     strart_frame   frames_length  filename.ext    123    456    [12]
 There can be a *stereoscopic* parallax positive/negative/0 parameter ("Z").
 Subtitle images' filenames must be pathless (will be searched for in the same
 path as subtitle file) and contain only alphanumeric characters plus "+-_ ".
 Subtitles' timing will be also analyzed for consistency (no overlapping). 

       title.ext   subtitling text file to check and/or apply edit(s) to
          leadIn   first subtitle # to apply edit to (default: first one)
         leadOut   last subtitle # to apply edit to (default: last one)
 [hh:]mm:ss[.ff]   TimeCode to shift subtitle(s) by
            Nfps   (or NHz) sets timecode to N frames/second (default: 24Hz)
               x   horizontal subtitle(s) padding
               y   vertical subtitle(s) padding
               z   stereoscopic depth ('=' sets it, otherwise offsets it)
          offset   number of pixels to pad subtitle(s) by
           --noz   removes subtitles' stereoscopic depth if present (3D to 2D) 
           --txt   Forces subtitle file output in .TXT format
           --scr   Forces subtitle file output in .SCR format"""
	exit(65)

mul, scale, drop, hasZ = 16, 24., False, None
subTCre = re.compile(r"(?P<hh>\d{1,2}):(?P<mm>\d{1,2}):(?P<ss>\d{1,2}):(?P<ff>\d{1,2})")
subre = re.compile(r"\s*(?P<ihh>\d{1,2}):(?P<imm>\d{1,2}):(?P<iss>\d{1,2}):(?P<iff>\d{1,2})\s+(?P<ohh>\d{1,2}):(?P<omm>\d{1,2}):(?P<oss>\d{1,2}):(?P<off>\d{1,2})\s+(?P<file>[a-zA-Z0-9_+.\ \-]+)\s+(?P<posX>\d+)\s+(?P<posY>\d+)(?:\s+(?P<posZ>[-+]?\d+))?")
scrre = re.compile(r"\s*(?P<start>\d+)\s+(?P<length>\d+)\s+(?P<file>[a-zA-Z0-9_+.\ \-]+)\s+(?P<posX>\d+)\s+(?P<posY>\d+)(?:\s+(?P<posZ>[-+]?\d+))?")

print "subman %s - TXT- and SCR-format 2D & 3D Subtitles command-line manager"%VERSION
print "Copyright (C) 2010 Walter Arrighetti for Technicolor Creative Services\n"


if not (1<len(sys.argv)<8):	syntax()

header, subt, subtitle, subt_num = [], [], [], 0
missing_files, wrong_subs = 0, 0
# Parses first argument in the command-line searching for subtitles.
try:
	if os.path.isfile(sys.argv[1]):
		(path,filename) = os.path.split(os.path.abspath(sys.argv[1]))
		format = os.path.splitext(filename)[-1]
		if format.startswith("."):
			format = format[1:].lower()
			if format not in ["txt","scr"]:	format = "txt"
		else:	format = "txt"
		infile = open(sys.argv[1],"r")
	else:	raise GeneralException
	indata = infile.readlines()
	infile.close()
except:
	print "  * ERROR!:  Unable to open source file %s !"%sys.argv[1]
	exit(2)

Oformat = format

if format=="txt":	
	for l in xrange(len(indata)):			# Separates header from subtitle lines
		if indata[l].expandtabs(0).startswith('#') and not subt:
			header.append(indata[l])
		elif subre.match(indata[l]):	subt.append(indata[l])
elif format=="scr":
	for l in xrange(len(indata)):
		if scrre.match(indata[l]):	subt.append(indata[l])
del indata


for l in xrange(len(subt)):			# Parses each subtitle and puts them in list of 5-tuples
	if format=="txt":	sre = subre.match(subt[l])
	elif format=="scr":	sre = scrre.match(subt[l])
	if not sre:
		print "  !sub# %d:  Invalid or malformed subtitle specification."%(l+1)
		wrong_subs += 1
	if hasZ==None:
		if format=="txt":
			if sre.groups()[11]:	hasZ = True
			else:	hasZ = False
		elif format=="scr":
			if sre.groups()[5]:	hasZ = True
			else:	hasZ = False
	else:
		if hasZ:
			if (format=="txt" and not sre.groups()[11]) or (format=="scr" and not sre.groups()[5]):
				print "  !sub# %d:  Parallax expected for a 3D subtitle"%(l+1)
				wrong_subs += 1
		elif not hasZ:
			if (format=="txt" and sre.groups()[11]) or (format=="scr" and sre.groups()[5]):
				print "  !sub# %d:  Unexpected parallax for a 2D subtitle"%(l+1)
				wrong_subs += 1
	if format=="txt":
		TCin  = TC2frame("%s:%s:%s.%s"%(sre.group('ihh'),sre.group('imm'),sre.group('iss'),sre.group('iff')), fps, signed=True)
		TCout = TC2frame("%s:%s:%s.%s"%(sre.group('ohh'),sre.group('omm'),sre.group('oss'),sre.group('off')), fps, signed=True)
	else:
		TCin = int(sre.group('start'))
		TCout = TCin + int(sre.group('length'))
	subfile = sre.group('file')
	posX, posY = int(sre.group('posX')), int(sre.group('posY'))
	if hasZ:	posZ = int(sre.group('posZ'))
	else:	posZ = None
	if format=="txt":
		subtitle.append([TCin, TCout, subfile, posX, posY, posZ, int(sre.group('iff')),int(sre.group('off'))])
	elif format=="scr":
		subtitle.append([TCin, TCout, subfile, posX, posY, posZ, None,None])
subt_num = len(subtitle)
leadIn, leadOut = 1, subt_num


# Parses other arguments in the command-line
for arg in sys.argv[2:]:
	if arg.lower()=="--txt":	Oformat = "txt"
	elif arg.lower()=="--scr":	Oformat = "scr"
	elif arg.lower()=="--noz":	noZ = True
	elif len(arg)>2 and (arg[0] in '+-') and re.match(r"((?P<hh>\d+)[:;])?(?P<mm>\d{1,2})(?P<drop>[:;])(?P<ss>\d{1,2})(\.(?P<ff>\d{1,2}))?", arg[1:]):
		continue			# Since scan mode could not have been parsed yet, restrains from parsing timecode
	elif len(arg)>2 and arg[-2:].lower()=='hz' and arg[:-2].isdigit():
		fps = int(arg[:-2])
	elif len(arg)>3 and arg[-3:].lower()=='fps' and arg[:-3].isdigit():
		fps = int(arg[:-3])
	elif arg.isdigit():
		leadIn = leadOut = int(arg)
	elif len(arg)>2 and arg[-1]=='-' and arg[:-1].isdigit():
		leadIn, leadOut = int(arg[:-1]), subt_num
	elif len(arg)>2 and arg[0]=='-' and arg[1:].isdigit():
		leadIn, leadOut = 1, int(arg[1:])
	elif re.match(r"(?P<leadIn>\d+)-(?P<leadOut>\d+)",arg):
		leaders = re.match(r"(?P<leadIn>\d+)-(?P<leadOut>\d+)",arg)
		leadIn, leadOut = int(leaders.group('leadIn')), int(leaders.group('leadOut'))
	elif len(arg)>2 and arg[0].lower()=='x' and arg[1] in '+-' and arg[2:].isdigit():
		if arg[1]=='+':	padX = int(arg[2:])
		else:	padX = -int(arg[2:])
	elif len(arg)>2 and arg[0].lower()=='y' and arg[1] in '+-' and arg[2:].isdigit():
		if arg[1]=='+':	padY = int(arg[2:])
		else:	padY = -int(arg[2:])
	elif len(arg)>2 and arg[0].lower()=='z' and arg[2:].isdigit():
		if arg[1] in '+-':	padZ = int(arg[1:])
		elif arg[1]=='=':	set_Z, padZ = int(arg[2:]), None
		else:	syntax()
	else:	syntax()
for arg in sys.argv[2:]:		# Specifically parsing of TimeCode shifts
	if len(arg)>2 and (arg[0] in '+-') and re.match(r"((?P<hh>\d+)[:;])?(?P<mm>\d{1,2})(?P<drop>[:;])(?P<ss>\d{1,2})(\.(?P<ff>\d{1,2}))?", arg[1:]):
		TC = TC2frame(arg,fps,signed=True)

# Prints the action to perform (and checks if affected range is OK).
if not (0 < leadIn <= leadOut <= subt_num):
	print "  * ERROR!: Subtitles' affected range [%d, %d] inconsistent\n            with input file's subtitle range [%d, %d] !"%(leadIn,leadOut,1,subt_num)
	exit(2)
elif len(sys.argv)>2 and (TC or padX or padY or padZ or set_Z):
	if leadIn==leadOut:	outstr = "Subtitle #%d"%leadIn
	elif leadIn==1 and leadOut==subt_num:
		outstr = "All %d subtitles"%subt_num
	elif leadIn==1 and leadOut!=subt_num:
		outstr = "First %d subtitles"%leadOut
	elif leadIn!=1 and leadOut==subt_num:
		outstr = "Last %d subtitles"%(subt_num-leadIn+1)
	else:	outstr = "Subtitles [%d, %d]"%(leadIn, leadOut)
	outstr += " will be"
	if TC:
		if TC>0:	outstr += " delayed"
		elif TC<0:	outstr += " anticipated"
		outstr += " by %s (@ %dHz)"%(frame2TC(abs(TC),fps,fulldispl=True),fps)
	if TC and (padX or padY):
		if padX and padY:	outstr += ","
		else:	outstr += " and"
	if padX or padY:
		outstr += " padded"
		if padX>0:	outstr += " right by %d"%padX
		elif padX<0:	outstr += " left by %d"%-padX
		if padX and padY:	outstr += " and"
		if padY>0:	outstr += " down by %d"%padY
		elif padY<0:	outstr += " up by %d"%-padY
		outstr += " pixels"
	if noZ and hasZ:	outstr += " stereoscopics removed"
	elif (not noZ):
		if TC or padX or padY:	outstr += " and"
#		outstr += ".\n\r"
		if hasZ and (padZ or set_Z):
			if padZ and not set_Z:	outstr += " parallax shifted by %r"%padZ
			elif set_Z and not padZ:	outstr += " parallax set to %r"%set_Z
		elif (not hasZ) and (not padZ) and set_Z:
			outstr += " added parallax as %r"%set_Z
	outstr += "."
	print outstr
elif len(sys.argv)>2 and not (TC or padX or padY or padZ or set_Z):
	print "  * WARNING!: Subtitle range [%d, %d] selected but no actions prescribed."%(leadIn,leadOut)


# Checks for inconsistencies:
#  * missing or empty subtitle images files,
#  * input timecodes not consistent with (prescribed) scan mode,
#  * overlapping or zero-duration subtitles,
#  * subtitle image files' panning (if ever) resulting in negative offsets
#  * timecode shift (if ever) making other timecodes overlap or fall behind 0-timecode.
for l in xrange(subt_num):
	if not os.path.isfile(os.path.join(path,subtitle[l][2])):
		print '  !sub# %d:  Image "%s" not found.'%(l+1,subtitle[l][2])
		missing_files += 1
	elif not os.path.getsize(os.path.join(path,subtitle[l][2])):
		print '  !sub# %d:  Image "%s" is empty.'%(l+1,subtitle[l][2])
		missing_files += 1
	if format=="txt" and (subtitle[l][5]>=fps  or  subtitle[l][6]>=fps):
		print "  !sub# %d:  TimeCode(s) not compatible with %dHz scan."%(l+1,fps)
		wrong_subs += 1
	if subtitle[l][0] < 0  or  subtitle[l][1] < 0:
		print "  !sub# %d:  Subtitle event on negative timecodes."%(l+1)
		wrong_subs += 1
	if subtitle[l][0] == subtitle[l][1]:
		print "  !sub# %d:  Zero-duration subtitle."%(l+1)
		wrong_subs += 1
	elif subtitle[l][0] > subtitle[l][1]:
		print "  !sub# %d:  Subtitle ends *before* beginning."%(l+1)
		wrong_subs += 1
	if l>0  and  subtitle[l][0] <= subtitle[l-1][1]:
		print "  !sub# %d:  Subtitle begins *before* (or when) previous one ends."%(l+1)
		wrong_subs += 1
	if (leadIn-1 <= l < leadOut)  and  subtitle[l][3] + padX < 0:
		print "  !sub# %d:  Subtitle image Horizontally padded to position %d."%(l+1,subtitle[l][3]+padX)
		wrong_subs += 1
	if (leadIn-1 <= l < leadOut)  and  subtitle[l][4] + padY < 0:
		print "  !sub# %d:  Subtitle image Vertically padded to position %d."%(l+1,subtitle[l][4]+padY)
		wrong_subs += 1
if wrong_subs or missing_files:			# Prints warning lines for subtitle inconsistencies.
	print "\n",
	if wrong_subs:	print "  * WARNING!: %d/%d subtitle timing/position mismatch(es) found."%(wrong_subs,subt_num)
	if missing_files:	print "  * WARNING!: %d/%d subtitle images either 0-length or not found."%(missing_files,subt_num)
	print "\n",
if TC<0  and  TC+subtitle[leadIn-1][0] < 0:
		print "  * ERROR!:  Prescribed TimeCode shift (%s) leads before 0-timecode."%frame2TC(TC,fps,fulldispl=True,signed=True)
		exit(3)
elif (leadIn>1  and  TC+subtitle[leadIn-1][0] <= subtitle[leadIn-2][1])  or  (leadOut<subt_num  and  TC+subtitle[leadOut-1][1] >= subtitle[leadOut][0]):
		print "  * ERROR!: Prescribed TimeCode shift (%s) makes subtitles overlap."%frame2TC(TC,fps,fulldispl=True,signed=True)
		exit(3)

#print "\n",
if TC or padX or padY or padZ or set_Z or format!=Oformat:
	if not padZ:	padZ = 0
	edit = []
	for l in xrange(subt_num):
		if (not hasZ) and subtitle[l][5]==None:	subtitle[l][5] = 0
		if leadIn-1 <= l < leadOut:
			if Oformat=="txt":
				edit.append([
					frame2subTC(TC + subtitle[l][0], fps, signed=True, fulldispl=True), 
					frame2subTC(TC + subtitle[l][1], fps, signed=True, fulldispl=True), 
					subtitle[l][2], 
					padX + subtitle[l][3], 
					padY + subtitle[l][4],
					padZ + subtitle[l][5]
				])
			elif Oformat=="scr":
				edit.append([
					subtitle[l][0], 
					subtitle[l][1] - subtitle[l][0] + 1, 
					subtitle[l][2], 
					padX + subtitle[l][3], 
					padY + subtitle[l][4],
					padZ + subtitle[l][5]
				])
			if set_Z:	edit[-1][5] = set_Z
		else:
			if Oformat=="txt":
				edit.append([
					frame2subTC(subtitle[l][0], fps, fulldispl=True), 
					frame2subTC(subtitle[l][1], fps, fulldispl=True), 
					subtitle[l][2], 
					subtitle[l][3], 
					subtitle[l][4],
					subtitle[l][5]
				])
			elif Oformat=="scr":
				edit.append([
					subtitle[l][0], 
					subtitle[l][1] - subtitle[l][0] + 1, 
					subtitle[l][2], 
					subtitle[l][3], 
					subtitle[l][4],
					subtitle[l][5]
				])
	outfname = '_'+os.path.splitext(filename)[0]+'.'+Oformat
#	try:
	outfile = open(os.path.join(path,outfname),"w")
	if Oformat=="txt":
		outfile.writelines(header)
		for l in xrange(subt_num):
			print edit[l]
			if (not noZ) and (padZ!=0 or set_Z):
				outfile.write("%s\t%s\t%s\t%d\t%d\t%d\n"%tuple(edit[l]))
			else:	outfile.write("%s\t%s\t%s\t%d\t%d\n"%edit[l][:-1])
	elif Oformat=="scr":
		for l in xrange(subt_num):
			if (not noZ) and (padZ!=0 or set_Z):
				outfile.write("%d %d %s %d %d %d\n"%edit[l])
			else:	outfile.write("%d %d %s %d %d\n"%edit[l][:-1])
	outfile.close()
	print 'New subtitles file "%s" saved in: %s'%(outfname,os.path.abspath(path))
#	except:
#		print '  * ERROR!: Unable to save file "%s" in: %s'%(outfname,os.path.abspath(path))
#		exit(2)


#if wrong_subs or missing_files:	exit(1)
elif not (TC or padX or padY):
	if hasZ:	print "Stereoscopic",
	else:	print "2D",
	print 'subtitle file "%s" syntactically & chronologically correct.'%filename
exit(0)
