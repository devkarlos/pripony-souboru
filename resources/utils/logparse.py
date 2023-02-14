import sys

filename = sys.argv[1] if len(sys.argv) > 1 else "test.txt"

SIG = "> HIT "
with open(filename, "r") as f:
	lines = f.readlines()

types = {}
matches = {}

for line in lines:
	if not line.startswith(SIG):
		continue
	line = line[len(SIG):].strip().split(";")
	assert len(line) == 2

	# remove of PE(hdr)...
	left = line[0].split("(")[0]
	right = line[1].split("(")[0]
	types[left] = None
	types[right] = None
	if left not in matches:
		matches[left] = []
	matches[left].append(right)


# adding non-generic polyglots
# matches["MP4"].append("PS") # handmade, but overlapping polyglot!
matches["DCM"].append("PE") # made by specific script
matches["PDF"].append("PE") # made by specific script


types = sorted(types) #, key=str.casefold)

# tolerated at any offset
AnyOffset = ["Zip", "7Z", "Arj", "RAR",]

# start with unverified space
Cavities = [
	"PDF",
	"ISO",
	"DCM",
	"TAR",
]

# Appended data not tolerated
NoAppData = ["BPG", "Java", "PCAP", "PCAPNG", "WASM",]

# required a strict footer
Footer = ["ID3v1", "XZ",]

# start of the file is parsed but magic not enforced at zero
Delayed = ["PS", "MP4",]

# general case:
# - Magic signature enforced at zero
# - appended data is tolerated
# - parasite tolerated
General = [
"AR", "BMP", "BZ2", "CAB", "CPIO", "EBML", "ELF", "FLV", "Flac", "GIF", "GZ",
"ICC", "ICO", "ID3v2", "ILDA", "JP2", "JPG", "NES", "OGG", "PSD", "LNK",
"PE", "PNG", "RIFF", "RTF", "TIFF", "WAD",
]

All = []
for l in [
	AnyOffset,
	Cavities,
	Delayed,
	General,
	NoAppData,
	Footer,
]:
	All.extend([" "] + l)

# 1:PS 2:PE 5:JPG 8:Flac/MP4/TIFF 9:FLV/Java 12:WAD/WASM 16:BPG/GIF/GZ/NES/PNG
# 20:ID3v2/RIFF 23:RTF 26:BMP 28:CPIO/OGG 30:Zip 32:ILDA 34:PSD 36:CAB
# 40:JP2/PCAPNG 48:PDF 64:ELF 68:AR 94:PCAP 112:ICO 132:ICC 352:DCM 512:TAR

Offsets = [
	[  1: "PS"],
	[  2: "PE"],
	[  5: "JPG"],
	[  8: "Flac"],
	[  8: "MP4"],
	[  8: "TIFF"],
	[  9: "FLV"],
	[ 12: "WAD"],
	[ 12: "WASM"],
	[ 16: "BPG"],
	[ 16: "GIF"],
	[ 16: "GZ"],
	[ 16: "NES"],
	[ 16: "PNG"],
	[ 20: "ID3v2"],
	[ 20: "RIFF"],
	[ 23: "RTF"],
	[ 26: "BMP"],
	[ 28: "CPIO"],
	[ 28: "OGG"],
	[ 30: "Zip"],
	[ 32: "ILDA"],
	[ 34: "PSD"],
	[ 36: "CAB"],
	[ 40: "JP2"],
	[ 40: "PCAPNG"],
	[ 48: "PDF"],
	[ 64: "ELF"],
	[ 68: "AR"],
	[ 94: "PCAP"],
	[112: "ICO"],
	[132: "ICC"],
	[144: "DCM"],
	[226: "Java"],
	[512: "TAR"],
]

lines = list([None]*5)

for i in range(5):
	lines[i] = []
	for t in All:
		c = t[i:i+1]
		c = " " if c == "" else c
		lines[i].append(c)
	print("".ljust(5), " ".join(lines[i]))


countall = 0
for left in All:
	textline = []
	for top in All:
		if left == top and len(left) > 1:
			textline.append(".")
			continue
		if (left in matches and top in matches[left]) or (top in matches and left in matches[top]):
			textline.append("X")
		else:
			textline.append(" ")
	textline = " ".join(textline)

	count = ""
	if textline.count(".") != 0:
		count = textline.count("X")
		countall += count
		count = "%2i" % count

	print(left[:5].ljust(5), textline, count)
print()
print("Formats combinations: %i" % (countall // 2))
