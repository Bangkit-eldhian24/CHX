#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  CHX — Cipher · Executor                                         ║
║  Enkripsi · Dekripsi · Obfuskasi · File Reader                   ║
║                                                                  ║
║  USAGE:                                                          ║
║    chx.py                          → Interactive mode            ║
║    chx.py -h                       → Help                        ║
║    chx.py -f file.txt -c caesar -s 3 -o out.txt                  ║
║    chx.py -f file.txt -de caesar -s 3 -o out.txt                 ║
║    chx.py -f file.bin -re -o dump.txt                            ║
║    chx.py -f file.txt -c obfuscate -o out.txt                    ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sys, os, re, base64, codecs, json, time, argparse, struct, math
from pathlib import Path
from collections import Counter
from datetime import datetime

# ══════════════════════════════════════════════════════════════════
#  Color scheme
# ══════════════════════════════════════════════════════════════════
class C:
    CYAN    = '\033[96m'
    GREEN   = '\033[92m'
    RED     = '\033[91m'
    YELLOW  = '\033[93m'
    MAGENTA = '\033[95m'
    DIM     = '\033[90m'
    BOLD    = '\033[1m'
    RESET   = '\033[0m'
    BLUE    = '\033[94m'
    ORANGE  = '\033[38;5;208m'
    WHITE   = '\033[97m'

def clr(t, c): return f"{c}{t}{C.RESET}"
def hr(n=64, ch='─'): return clr(ch * n, C.DIM)
def ok(msg):    print(clr(f"  ✔ {msg}", C.GREEN))
def warn(msg):  print(clr(f"  ⚠ {msg}", C.YELLOW))
def err(msg):   print(clr(f"  ✖ {msg}", C.RED));
def info(msg):  print(clr(f"  ℹ {msg}", C.CYAN))

def fmt_size(n):
    for u in ['B','KB','MB','GB','TB']:
        if n < 1024: return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PB"

def fmt_time(s):
    return f"{s:.1f}s" if s < 60 else f"{int(s//60)}m {s%60:.0f}s"

# ══════════════════════════════════════════════════════════════════
#  BANNER
# ══════════════════════════════════════════════════════════════════
BANNER = clr(r"""
   ██████╗██╗  ██╗██╗  ██╗
  ██╔════╝██║  ██║╚██╗██╔╝
  ██║     ███████║ ╚███╔╝
  ██║     ██╔══██║ ██╔██╗
  ╚██████╗██║  ██║██╔╝ ██╗
   ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝
""", C.CYAN) + clr("  Cipher · Executor  v1.0\n", C.DIM)

def banner():
    os.system('clear' if os.name == 'posix' else 'cls')
    print(BANNER)
    print(hr())

# ══════════════════════════════════════════════════════════════════
#  CIPHER FUNCTIONS
# ══════════════════════════════════════════════════════════════════

def caesar(text, shift, decrypt=False):
    if decrypt: shift = (26 - shift) % 26
    return ''.join(
        chr((ord(c)-(97 if c.islower() else 65)+shift)%26+(97 if c.islower() else 65))
        if c.isalpha() else c for c in text
    )

class VigState:
    def __init__(self, key, decrypt=False):
        self.key  = [c for c in key.upper() if c.isalpha()]
        self.dec  = decrypt
        self.pos  = 0
    def run(self, text):
        if not self.key: return text
        out = []
        for c in text:
            if c.isalpha():
                base = 97 if c.islower() else 65
                k = ord(self.key[self.pos % len(self.key)]) - 65
                if self.dec: k = -k
                out.append(chr((ord(c)-base+k)%26+base))
                self.pos += 1
            else:
                out.append(c)
        return ''.join(out)

def vigenere(text, key, decrypt=False):
    return VigState(key, decrypt).run(text)

def rot13(text):   return codecs.encode(text, 'rot_13')
def atbash(text):
    return ''.join(
        chr((97 if c.islower() else 65)+25-(ord(c)-(97 if c.islower() else 65)))
        if c.isalpha() else c for c in text
    )

def to_b64(text):   return base64.b64encode(text.encode('utf-8','replace')).decode()
def from_b64(text):
    try:
        t = text.strip().replace('\n','').replace(' ','')
        t += '='*(-len(t)%4)
        return base64.b64decode(t).decode('utf-8','replace')
    except: return "[ERROR: bukan Base64]"

def to_hex(text):   return text.encode('utf-8','replace').hex()
def from_hex(text):
    try: return bytes.fromhex(text.strip().replace(' ','').replace('0x','')).decode('utf-8','replace')
    except: return "[ERROR: bukan Hex]"

def to_bin(text):   return ' '.join(format(b,'08b') for b in text.encode('utf-8','replace'))
def from_bin(text):
    try:
        bits = text.strip().split()
        return bytes(int(b,2) for b in bits).decode('utf-8','replace')
    except: return "[ERROR: bukan Binary]"

MORSE = {
    'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....','I':'..','J':'.---',
    'K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-','R':'.-.','S':'...','T':'-',
    'U':'..-','V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..',
    '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....',
    '6':'-....','7':'--...','8':'---..','9':'----.',
    '.':'.-.-.-',',':'--..--','?':'..--..','!':'-.-.--',
}
MORSE_R = {v:k for k,v in MORSE.items()}
def to_morse(text):
    return ' '.join('/' if c==' ' else MORSE.get(c.upper(),f'<{c}>') for c in text)
def from_morse(text):
    try:
        return ' '.join(''.join(MORSE_R.get(t,'?') for t in w.split() if t)
                        for w in text.strip().split(' / '))
    except: return "[ERROR: Morse tidak valid]"

# ── Obfuskasi ────────────────────────────────────────────────────
LEET_E = {'a':'4','e':'3','i':'1','o':'0','t':'7','s':'5','g':'9','b':'8','l':'|',
           'A':'4','E':'3','I':'1','O':'0','T':'7','S':'5','G':'9','B':'8','L':'|'}
LEET_D = {'4':'a','3':'e','1':'i','0':'o','7':'t','5':'s','9':'g','8':'b','|':'l'}
UNI    = {'a':'а','e':'е','o':'о','p':'р','c':'с','x':'х','i':'і'}

def leet(text, lv=1):
    return ''.join((LEET_E.get(c,c) if (lv==2 or c.lower() in 'aeiou') else c) for c in text)
def unleet(text): return ''.join(LEET_D.get(c,c) for c in text)
def homoglyph(text): return ''.join(UNI.get(c,c) for c in text)
def rev_lines(text): return '\n'.join(l[::-1] for l in text.split('\n'))
def zalgo(text, n=2):
    import random; random.seed(42)
    comb = ['\u0300','\u0301','\u0302','\u0303','\u0308','\u0332','\u0333','\u0334','\u0335']
    out = []
    for c in text:
        out.append(c)
        if c.isalpha():
            for _ in range(n): out.append(random.choice(comb))
    return ''.join(out)

def xor_enc(text, key):
    raw = text.encode('utf-8','replace')
    kb  = key.encode('utf-8')
    return bytes(b ^ kb[i%len(kb)] for i,b in enumerate(raw)).hex()

def xor_dec(hex_text, key):
    try:
        raw = bytes.fromhex(hex_text.strip())
        kb  = key.encode('utf-8')
        return bytes(b ^ kb[i%len(kb)] for i,b in enumerate(raw)).decode('utf-8','replace')
    except: return "[ERROR: XOR/Hex tidak valid]"

# ── Readability ──────────────────────────────────────────────────
WORDS = ["yang","dan","ini","itu","ke","di","dari","untuk","pada","dengan","tidak","ada",
         "selamat","farida","the","and","for","are","you","can","flag","ctf","key","hello",
         "ayam","goreng","mail","username","password","user","role","secret","token"]

def score(text):
    if not text or 'ERROR' in str(text): return 0.0
    t = text.lower(); s = 0.0
    for w in WORDS:
        if w in t: s += 12
    letters = [c.upper() for c in t if c.isalpha()]
    if not letters: return 0.0
    freq = Counter(letters); total = sum(freq.values())
    for i,ch in enumerate("ETAOINSHRDLCUMWFGYPBVKJXQZ"[:10]):
        if ch in freq: s += (10-i)*(freq[ch]/total)
    s += text.count(' ')*0.8
    s -= sum(1 for c in text if ord(c)>127 or (ord(c)<32 and c not in '\n\t\r'))*2
    return s

# ══════════════════════════════════════════════════════════════════
#  BINARY / UNREADABLE FILE READER (-re)
# ══════════════════════════════════════════════════════════════════

# Magic bytes → file type
MAGIC = {
    b'\x4d\x5a': 'Windows PE/EXE',
    b'\x7fELF': 'ELF Executable (Linux/Android)',
    b'\x4c\x00\x00\x00': 'Windows Shortcut (.lnk)',
    b'\xff\xd8\xff': 'JPEG Image',
    b'\x89PNG': 'PNG Image',
    b'GIF8': 'GIF Image',
    b'%PDF': 'PDF Document',
    b'PK\x03\x04': 'ZIP/DOCX/XLSX/APKK Archive',
    b'\x1f\x8b': 'GZIP Archive',
    b'BZh': 'BZIP2 Archive',
    b'\xd0\xcf\x11\xe0': 'MS Office (old format)',
    b'RIFF': 'RIFF (WAV/AVI)',
    b'fLaC': 'FLAC Audio',
    b'ID3': 'MP3 Audio',
    b'\x00\x00\x00\x20ftyp': 'MP4 Video',
    b'SQLite': 'SQLite Database',
    b'{\x22': 'JSON',
    b'<?xm': 'XML',
    b'<!DO': 'HTML',
}

def detect_filetype(data: bytes) -> str:
    for magic, name in MAGIC.items():
        if data.startswith(magic): return name
    # UTF-16 LE check
    if data[:2] == b'\xff\xfe': return 'UTF-16 LE Text'
    if data[:2] == b'\xfe\xff': return 'UTF-16 BE Text'
    # Check if mostly printable
    printable = sum(1 for b in data[:512] if 0x20 <= b <= 0x7e or b in (9,10,13))
    ratio = printable / min(len(data), 512)
    if ratio > 0.9: return 'Plain Text'
    if ratio > 0.6: return 'Mixed Binary/Text'
    return 'Binary Data'

def extract_strings(data: bytes, min_len=4) -> list:
    """Ekstrak readable ASCII strings dari binary."""
    results = []
    cur = []
    for b in data:
        if 0x20 <= b <= 0x7e or b in (9, 10, 13):
            cur.append(chr(b))
        else:
            s = ''.join(cur).strip()
            if len(s) >= min_len:
                results.append(s)
            cur = []
    s = ''.join(cur).strip()
    if len(s) >= min_len: results.append(s)
    return results

def extract_utf16_strings(data: bytes, min_len=4) -> list:
    """Ekstrak UTF-16 LE strings (umum di Windows binary)."""
    results = []
    cur = []
    i = 0
    while i < len(data)-1:
        word = data[i:i+2]
        if word[1] == 0 and 0x20 <= word[0] <= 0x7e:
            cur.append(chr(word[0]))
            i += 2
        else:
            s = ''.join(cur).strip()
            if len(s) >= min_len: results.append(s)
            cur = []
            i += 1
    return results

def detect_jwt(text: str):
    """Deteksi dan decode JWT token."""
    pattern = r'eyJ[A-Za-z0-9_\-]+\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+'
    matches = re.findall(pattern, text)
    results = []
    for jwt in matches:
        parts = jwt.split('.')
        if len(parts) >= 2:
            try:
                header  = json.loads(base64.urlsafe_b64decode(parts[0]+'=='))
                payload = json.loads(base64.urlsafe_b64decode(parts[1]+'=='))
                # Format timestamps
                for field in ['iat','exp','nbf']:
                    if field in payload:
                        try:
                            ts = datetime.fromtimestamp(payload[field])
                            payload[field+' (human)'] = ts.strftime('%Y-%m-%d %H:%M:%S')
                        except: pass
                results.append({'jwt': jwt[:40]+'...', 'header': header, 'payload': payload})
            except: pass
    return results

def detect_base64url(text: str) -> list:
    """Deteksi Base64 atau Base64URL dan decode."""
    found = []
    # Base64url pattern (JWT-like tapi bukan JWT)
    for match in re.finditer(r'[A-Za-z0-9+/=]{20,}', text):
        s = match.group()
        try:
            dec = base64.b64decode(s + '=='*2).decode('utf-8','strict')
            if score(dec) > 5 or dec.startswith('{'):
                found.append((s[:30]+'...', dec[:100]))
        except: pass
    return found

def read_binary(path: str, out_path: str = None):
    """
    Baca file binary / unreadable dan ekstrak semua informasi yang bisa dibaca.
    """
    print(clr(f"\n  ╔════════════════════════════════════════════════════════╗", C.MAGENTA))
    print(clr(f"  ║   📂  BINARY FILE READER                               ║", C.MAGENTA))
    print(clr(f"  ╚════════════════════════════════════════════════════════╝\n", C.MAGENTA))

    file_size = os.path.getsize(path)
    info(f"File  : {path}")
    info(f"Ukuran: {fmt_size(file_size)}")

    # Baca sample awal (max 50MB untuk analisis)
    sample_size = min(file_size, 50 * 1024 * 1024)
    with open(path, 'rb') as f:
        data = f.read(sample_size)

    # ── 1. Tipe file ──────────────────────────────────────────────
    ftype = detect_filetype(data)
    print(f"\n  {clr('[ FILE TYPE ]', C.YELLOW)}")
    print(f"  Tipe terdeteksi : {clr(ftype, C.GREEN)}")
    print(f"  Magic bytes     : {clr(data[:8].hex(), C.CYAN)}")

    output_lines = [
        f"CHX Binary File Reader — {path}",
        f"Tanggal: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Ukuran : {fmt_size(file_size)}",
        f"Tipe   : {ftype}",
        f"Magic  : {data[:8].hex()}",
        ""
    ]

    # ── 2. Entropy ────────────────────────────────────────────────
    freq = Counter(data[:4096])
    entropy = -sum((c/4096)*math.log2(c/4096) for c in freq.values() if c)
    enc_likelihood = "Kemungkinan TERENKRIPSI/COMPRESSED" if entropy > 7.0 else \
                     "Data terstruktur / campuran" if entropy > 5.0 else "Data teks/terstruktur"
    print(f"\n  {clr('[ ENTROPY ANALYSIS ]', C.YELLOW)}")
    print(f"  Entropy : {clr(f'{entropy:.3f}/8.000', C.CYAN)}")
    print(f"  Status  : {clr(enc_likelihood, C.GREEN if entropy < 7 else C.RED)}")
    output_lines += [f"Entropy: {entropy:.3f} — {enc_likelihood}", ""]

    # ── 3. Hex dump (pertama 256 bytes) ──────────────────────────
    print(f"\n  {clr('[ HEX DUMP — 256 bytes pertama ]', C.YELLOW)}")
    hex_lines = []
    for i in range(0, min(256, len(data)), 16):
        chunk = data[i:i+16]
        hex_part  = ' '.join(f'{b:02x}' for b in chunk)
        ascii_part = ''.join(chr(b) if 0x20<=b<=0x7e else '.' for b in chunk)
        line = f"  {i:08x}  {hex_part:<48}  |{ascii_part}|"
        print(clr(line, C.DIM))
        hex_lines.append(line.strip())
    output_lines += ["=== HEX DUMP (256 bytes pertama) ==="] + hex_lines + [""]

    # ── 4. ASCII Strings ──────────────────────────────────────────
    print(f"\n  {clr('[ READABLE ASCII STRINGS ]', C.YELLOW)}")
    strings = extract_strings(data)
    # Filter: hanya yang panjang >= 4 dan interesting
    interesting = [s for s in strings if len(s) >= 4][:200]
    if interesting:
        for s in interesting[:30]:
            print(f"  {clr('»', C.CYAN)} {clr(s[:100], C.GREEN)}")
        if len(interesting) > 30:
            warn(f"...{len(interesting)-30} strings lagi (lihat file output)")
    else:
        warn("Tidak ada ASCII string yang dapat dibaca")
    output_lines += ["=== ASCII STRINGS ==="] + [f"» {s}" for s in interesting] + [""]

    # ── 5. UTF-16 Strings (Windows binaries) ─────────────────────
    print(f"\n  {clr('[ UTF-16 STRINGS (Windows format) ]', C.YELLOW)}")
    utf16 = extract_utf16_strings(data)
    utf16_filtered = [s for s in utf16 if len(s) >= 4][:100]
    if utf16_filtered:
        for s in utf16_filtered[:20]:
            print(f"  {clr('◈', C.MAGENTA)} {clr(s[:100], C.YELLOW)}")
        if len(utf16_filtered) > 20:
            warn(f"...{len(utf16_filtered)-20} strings lagi (lihat file output)")
    else:
        warn("Tidak ada UTF-16 string ditemukan")
    output_lines += ["=== UTF-16 STRINGS ==="] + [f"◈ {s}" for s in utf16_filtered] + [""]

    # ── 6. Gabungkan semua strings, cari JWT / Base64 ─────────────
    all_text = '\n'.join(interesting + utf16_filtered)

    print(f"\n  {clr('[ JWT TOKEN DETECTION ]', C.YELLOW)}")
    jwts = detect_jwt(all_text)
    if jwts:
        for j in jwts:
            print(f"  {clr('JWT ditemukan:', C.GREEN)} {j['jwt']}")
            print(f"  {clr('Header  :', C.CYAN)}  {json.dumps(j['header'])}")
            print(f"  {clr('Payload :', C.CYAN)}  {json.dumps(j['payload'], indent=2)}")
        output_lines += ["=== JWT TOKENS ==="]
        for j in jwts:
            output_lines += [f"JWT: {j['jwt']}", f"Header: {json.dumps(j['header'])}",
                             f"Payload: {json.dumps(j['payload'], indent=2)}", ""]
    else:
        warn("Tidak ada JWT ditemukan")

    # ── 7. URL / Path / Email extraction ──────────────────────────
    print(f"\n  {clr('[ URL / PATH / EMAIL EXTRACTION ]', C.YELLOW)}")
    combined = all_text
    urls   = re.findall(r'https?://[^\s<>"\']+', combined)
    paths  = re.findall(r'[A-Za-z]:[\\][^\s\x00<>"|?*]+', combined)  # Windows paths
    lpaths = re.findall(r'/(?:usr|bin|etc|home|var|tmp|proc)/[^\s\x00<>"]+', combined)
    emails = re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', combined)
    regs   = re.findall(r'HKEY_[A-Z_\\]+', combined)

    for label, items in [("URL", urls), ("Windows Path", paths), ("Linux Path", lpaths),
                          ("Email", emails), ("Registry Key", regs)]:
        if items:
            for item in items[:10]:
                print(f"  {clr(f'[{label}]', C.ORANGE)} {clr(item[:120], C.WHITE)}")
    if not any([urls, paths, lpaths, emails, regs]):
        warn("Tidak ada URL/path/email ditemukan")

    output_lines += ["=== URLS & PATHS ==="]
    for label, items in [("URL",urls),("WinPath",paths),("LPath",lpaths),("Email",emails),("Reg",regs)]:
        for item in items[:20]: output_lines.append(f"[{label}] {item}")
    output_lines.append("")

    # ── 8. Versi / Build info ─────────────────────────────────────
    versions = re.findall(r'\d+\.\d+\.\d+[\.\d]*', combined)
    guids    = re.findall(r'\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\}', combined)
    if versions or guids:
        print(f"\n  {clr('[ VERSION / GUID ]', C.YELLOW)}")
        for v in set(versions[:10]): print(f"  {clr('version', C.DIM)} {clr(v, C.CYAN)}")
        for g in set(guids[:5]):     print(f"  {clr('GUID   ', C.DIM)} {clr(g, C.CYAN)}")
        output_lines += [f"Version: {v}" for v in set(versions[:10])]
        output_lines += [f"GUID: {g}" for g in set(guids[:5])]
        output_lines.append("")

    # ── 9. Base64 dalam strings ───────────────────────────────────
    print(f"\n  {clr('[ BASE64 / ENCODED STRINGS ]', C.YELLOW)}")
    b64_found = detect_base64url(combined)
    if b64_found:
        for orig, dec in b64_found[:5]:
            print(f"  {clr('B64', C.BLUE)}: {clr(orig, C.DIM)} → {clr(dec[:80], C.GREEN)}")
    else:
        warn("Tidak ada Base64 string yang bisa di-decode")
    output_lines += ["=== BASE64 DECODED ==="]
    for orig, dec in b64_found: output_lines.append(f"{orig} → {dec}")
    output_lines.append("")

    # ── 10. Summary ───────────────────────────────────────────────
    print(f"\n  {hr()}")
    print(f"  {clr('RINGKASAN:', C.BOLD+C.WHITE)}")
    print(f"  Tipe File    : {clr(ftype, C.CYAN)}")
    print(f"  Entropy      : {clr(f'{entropy:.3f}', C.CYAN)}")
    print(f"  ASCII str    : {clr(str(len(interesting)), C.GREEN)}")
    print(f"  UTF-16 str   : {clr(str(len(utf16_filtered)), C.GREEN)}")
    print(f"  JWT           : {clr(str(len(jwts)), C.YELLOW)}")
    print(f"  URL/Path      : {clr(str(len(urls+paths+lpaths)), C.YELLOW)}")
    print(f"  Sample size  : {clr(fmt_size(sample_size), C.DIM)} / {fmt_size(file_size)}")

    summary_lines = [
        "", "=== SUMMARY ===",
        f"File Type   : {ftype}",
        f"Entropy     : {entropy:.3f}",
        f"ASCII str   : {len(interesting)}",
        f"UTF-16 str  : {len(utf16_filtered)}",
        f"JWT         : {len(jwts)}",
        f"URL/Path    : {len(urls+paths+lpaths)}",
    ]
    output_lines += summary_lines

    # ── Tulis output ──────────────────────────────────────────────
    if out_path:
        with open(out_path, 'w', encoding='utf-8', errors='replace') as f:
            f.write('\n'.join(output_lines))
        ok(f"Output disimpan: {out_path}")

    return '\n'.join(output_lines)

# ══════════════════════════════════════════════════════════════════
#  STREAMING FILE PROCESSOR
# ══════════════════════════════════════════════════════════════════

# Chunk size sesuai -mod dan -med
MOD_SIZES = {
    '1': 100*1024*1024,   # 100 MB
    '2': 200*1024*1024,   # 200 MB
    '3': 300*1024*1024,   # 300 MB
    '4': 400*1024*1024,   # 400 MB
    '5': 500*1024*1024,   # 500 MB
}
MED_SIZE = 4*1024*1024    # default streaming chunk: 4 MB

FULL_LOAD_METHODS = {'base64','b64','hex','binary','bin','morse'}

def progress(done, total, t0, width=38):
    pct = done/max(total,1)
    filled = int(pct*width)
    bar = '█'*filled + '░'*(width-filled)
    elapsed = time.time()-t0
    speed = done/max(elapsed,0.001)
    eta = (total-done)/max(speed,1)
    print(f"\r  {clr(bar,C.CYAN)} {clr(f'{pct*100:5.1f}%',C.YELLOW)}"
          f"  {clr(fmt_size(done),C.DIM)}/{clr(fmt_size(total),C.DIM)}"
          f"  {clr(fmt_size(speed)+'/s',C.BLUE)}"
          f"  ETA {clr(fmt_time(eta),C.DIM)}", end='', flush=True)

class StreamState:
    """Stateful cipher wrapper untuk streaming."""
    def __init__(self, method, **kw):
        self.method = method.lower()
        self.kw = kw
        if self.method in ('vigenere','vigenere_dec'):
            self.vig = VigState(kw.get('key','KEY'), decrypt=('dec' in self.method))
        if self.method in ('xor','xor_dec'):
            self.key = kw.get('key','X').encode()
            self.pos = 0

    def run(self, chunk):
        m = self.method
        if   m == 'caesar':      return caesar(chunk, self.kw.get('shift',3))
        elif m == 'caesar_dec':  return caesar(chunk, self.kw.get('shift',3), True)
        elif m in ('vigenere','vigenere_dec'): return self.vig.run(chunk)
        elif m == 'rot13':       return rot13(chunk)
        elif m == 'atbash':      return atbash(chunk)
        elif m == 'leet1':       return leet(chunk, 1)
        elif m == 'leet2':       return leet(chunk, 2)
        elif m == 'unleet':      return unleet(chunk)
        elif m == 'homoglyph':   return homoglyph(chunk)
        elif m == 'rev_lines':   return rev_lines(chunk)
        elif m == 'xor':
            raw = chunk.encode('utf-8','replace')
            out = bytes(b ^ self.key[(self.pos+i)%len(self.key)] for i,b in enumerate(raw))
            self.pos = (self.pos+len(raw))%len(self.key)
            return out.hex()
        elif m == 'xor_dec':
            raw = bytes.fromhex(chunk.strip()) if re.fullmatch(r'[0-9a-fA-F\s]+',chunk.strip()) else b''
            out = bytes(b ^ self.key[(self.pos+i)%len(self.key)] for i,b in enumerate(raw))
            self.pos = (self.pos+len(raw))%len(self.key)
            return out.decode('utf-8','replace')
        return chunk

def detect_enc(path):
    """Deteksi encoding file."""
    try:
        with open(path,'rb') as f: raw = f.read(32768)
        if raw.startswith(b'\xff\xfe'): return 'utf-16-le'
        if raw.startswith(b'\xfe\xff'): return 'utf-16-be'
        if raw.startswith(b'\xef\xbb\xbf'): return 'utf-8-sig'
        raw.decode('utf-8'); return 'utf-8'
    except: return 'latin-1'

def process_file(input_path, output_path, state: StreamState,
                 chunk_size=MED_SIZE, enc='utf-8'):
    """Streaming file processor."""
    total = os.path.getsize(input_path)
    done  = 0
    t0    = time.time()

    info(f"Input  : {input_path}  ({fmt_size(total)})")
    info(f"Output : {output_path}")
    info(f"Metode : {state.method}  | Chunk: {fmt_size(chunk_size)}\n")

    # Full-load methods
    if state.method in FULL_LOAD_METHODS:
        if total > 50*1024*1024:
            warn(f"Metode ini memerlukan load penuh. File {fmt_size(total)} — perlu RAM besar.")
            if input(clr("  Lanjutkan? [y/N] > ", C.RED)).strip().lower() != 'y':
                warn("Dibatalkan."); return

        print(clr("  Membaca...", C.DIM), end=' ', flush=True)
        with open(input_path,'r',encoding=enc,errors='replace') as f: content = f.read()
        print(clr("OK",C.GREEN))
        print(clr("  Memproses...", C.DIM), end=' ', flush=True)

        fn = {'base64':to_b64,'b64':to_b64,'base64_dec':from_b64,'b64_dec':from_b64,
              'hex':to_hex,'hex_dec':from_hex,'binary':to_bin,'bin':to_bin,
              'binary_dec':from_bin,'bin_dec':from_bin,'morse':to_morse,'morse_dec':from_morse}
        result = fn.get(state.method, lambda x: x)(content)
        print(clr("OK",C.GREEN))
        with open(output_path,'w',encoding=enc,errors='replace') as f: f.write(result)

    else:
        # Streaming
        print()
        with open(input_path,'r',encoding=enc,errors='replace') as fin, \
             open(output_path,'w',encoding=enc,errors='replace') as fout:
            while True:
                chunk = fin.read(chunk_size)
                if not chunk: break
                done += len(chunk.encode(enc,'replace'))
                fout.write(state.run(chunk))
                progress(min(done,total), total, t0)
        print()

    elapsed = time.time()-t0
    out_sz  = os.path.getsize(output_path)
    ok(f"Selesai dalam {fmt_time(elapsed)}")
    info(f"Input  : {fmt_size(total)}  →  Output: {fmt_size(out_sz)}  ({fmt_size(total/max(elapsed,0.001))}/s)")
    ok(f"Tersimpan: {output_path}")

# ══════════════════════════════════════════════════════════════════
#  AUTO-DETECT
# ══════════════════════════════════════════════════════════════════

def auto_detect(text):
    """Brute-force decode dengan semua metode."""
    print(clr("\n  ╔══════════════════════════════════════════════════════╗", C.YELLOW))
    print(clr("  ║   🔍  AUTO-DETECT + MULTI-LAYER DECODE               ║", C.YELLOW))
    print(clr("  ╚══════════════════════════════════════════════════════╝\n", C.YELLOW))

    # Deteksi JWT dulu
    jwts = detect_jwt(text)
    if jwts:
        ok("JWT Token terdeteksi!")
        for j in jwts:
            print(f"\n  {clr('Header  :', C.CYAN)} {json.dumps(j['header'])}")
            print(f"  {clr('Payload :', C.CYAN)}")
            for k,v in j['payload'].items():
                print(f"    {clr(k,C.YELLOW)}: {clr(str(v),C.GREEN)}")
        print()

    results = []

    # Format-specific
    t = text.strip()
    tokens = t.split()

    if tokens and all(re.fullmatch(r'[01]{8}',tok) for tok in tokens[:8]):
        r = from_bin(text); results.append(('Binary','direct',r,score(r)+30))
        print(clr(f"  ⚡ Binary → {r[:60]}", C.CYAN))

    hx = t.replace(' ','').replace('0x','')
    if re.fullmatch(r'[0-9a-fA-F]+', hx) and len(hx)%2==0 and len(hx)>=4:
        r = from_hex(t); results.append(('Hex','direct',r,score(r)+20))

    b64 = t.replace('\n','').replace(' ','')
    if re.fullmatch(r'[A-Za-z0-9+/=]+',b64) and len(b64)%4==0 and len(b64)>=4:
        r = from_b64(t)
        if 'ERROR' not in r: results.append(('Base64','direct',r,score(r)+15))

    morse_t = [tok for tok in tokens if tok != '/']
    if morse_t and all(re.fullmatch(r'[.\-]+', tok) for tok in morse_t[:6]):
        r = from_morse(t); results.append(('Morse','direct',r,score(r)))

    # Morse-binary
    if morse_t and all(re.fullmatch(r'[.\-]{5}', tok) for tok in morse_t[:6]):
        try:
            bits = ''
            for w in t.split(' / '):
                for tok in w.strip().split():
                    if tok == '-----': bits += '0'
                    elif tok == '.----': bits += '1'
                    else: raise ValueError
            if bits and len(bits)%8==0:
                r = from_bin(' '.join(bits[i:i+8] for i in range(0,len(bits),8)))
                results.append(('Morse→Binary→ASCII','MULTI',r,score(r)+50))
                print(clr(f"  ⚡ [MULTI] Morse-Binary → {r[:60]}", C.YELLOW))
        except: pass

    # Standard brute force
    for s in range(1,26): results.append(('Caesar',f'shift={s}',caesar(t,s,True),score(caesar(t,s,True))))
    results.append(('ROT13','-',rot13(t),score(rot13(t))))
    results.append(('Atbash','-',atbash(t),score(atbash(t))))
    results.append(('De-Leet','-',unleet(t),score(unleet(t))))

    for k in ["CTF","FLAG","SECRET","FARIDA","CIPHER","KEY","ADMIN","KUNCI","INDONESIA","RAHASIA","HACK"]:
        r = vigenere(t,k,True); results.append(('Vigenère',f'key={k}',r,score(r)))

    results.sort(key=lambda x: x[3], reverse=True)

    print(clr("\n  TOP 10 KEMUNGKINAN\n", C.DIM))
    for i,(method,param,decoded,sc) in enumerate(results[:10], 1):
        bar = '█'*min(int(sc*0.8),20)+'░'*max(0,20-min(int(sc*0.8),20))
        is_multi = 'MULTI' in param or '→' in method
        rc = C.GREEN if i==1 else C.YELLOW if i<=3 else C.DIM
        mc = C.MAGENTA if is_multi else C.RESET
        tag = clr(' ◈MULTI',C.MAGENTA) if is_multi else ''
        print(clr(f"  [{i:2d}]",rc), end='')
        print(clr(f" {method:<22}",mc), end='')
        print(clr(f" {param:<16}",C.DIM), end='')
        print(f" {clr(bar,C.BLUE)} {clr(f'{sc:.1f}',C.YELLOW)}{tag}")
        print(f"       {clr((decoded[:70]+'...' if len(decoded)>70 else decoded), C.GREEN if sc>10 else C.DIM)}\n")

    best = results[0]
    print(clr("  ╔════════════════════════════════════════════════════════╗", C.GREEN))
    print(clr(f"  ║  ⭐ BEST MATCH: {best[0]} ({best[1]})", C.GREEN))
    print(clr("  ╚════════════════════════════════════════════════════════╝", C.GREEN))
    print(f"  {clr(best[2], C.GREEN)}\n")

    k = input(clr("  Coba Vigenère kustom? (kosong=skip) Key > ", C.DIM)).strip()
    if k: print(f"  {clr(vigenere(t,k,True), C.GREEN)}\n")

# ══════════════════════════════════════════════════════════════════
#  ARGUMENT PARSER (CLI mode)
# ══════════════════════════════════════════════════════════════════

HELP_TEXT = f"""
{BANNER}
{clr('USAGE:', C.YELLOW)}
  chx.py                                    Interactive mode
  chx.py -f input.txt -c caesar -s 3 -o out.txt
  chx.py -f input.txt -de caesar -s 3 -o out.txt
  chx.py -f input.txt -c vigenere -k MYKEY -o out.txt
  chx.py -f input.txt -c obfuscate -o out.txt
  chx.py -f input.bin -re -o dump.txt
  chx.py -f bigfile.txt -c rot13 -mod 2 -o out.txt
  chx.py -f huge.txt -c leet -med -o out.txt

{clr('FLAGS:', C.YELLOW)}
  -f   FILE      Input file (semua format teks, atau binary untuk -re)
  -o   FILE      Output file (default: input_chx.ext)
  -c   METHOD    Enkripsi/Obfuskasi:
                   caesar, vigenere, rot13, atbash, base64, hex,
                   binary, morse, leet, leet2, xor, homoglyph,
                   rev, zalgo, obfuscate (menu pilih)
  -de  METHOD    Dekripsi/De-Obfuskasi (metode sama dengan -c):
                   caesar, vigenere, base64, hex, binary, morse,
                   leet, xor, auto (auto-detect)
  -s   N         Shift value (Caesar, default: 3)
  -k   KEY       Key string (Vigenère, XOR)
  -re            Read/extract unreadable binary file
  -mod N         Chunk mode 1-5 (100MB/200MB/300MB/400MB/500MB per chunk)
  -med           Medium mode: 4MB chunk, optimal untuk file 500MB-10GB
  -prev          Preview file sebelum proses (10 baris pertama)
  -h             Help ini

{clr('CONTOH:', C.CYAN)}
  chx.py -f secret.txt -c caesar -s 7 -o encrypted.txt
  chx.py -f encrypted.txt -de caesar -s 7 -o decrypted.txt
  chx.py -f data.txt -c vigenere -k FARIDA -o out.txt
  chx.py -f data.txt -de vigenere -k FARIDA -o out.txt
  chx.py -f file.bin -re -o analysis.txt
  chx.py -f huge.log -c xor -k SECRET -mod 3 -o out.txt
  chx.py -f token.txt -de auto
"""

def build_parser():
    parser = argparse.ArgumentParser(prog='chx.py', add_help=False)
    parser.add_argument('-f',   dest='file',   default=None)
    parser.add_argument('-o',   dest='output', default=None)
    parser.add_argument('-c',   dest='cipher', default=None)
    parser.add_argument('-de',  dest='decode', default=None)
    parser.add_argument('-s',   dest='shift',  type=int, default=3)
    parser.add_argument('-k',   dest='key',    default='KEY')
    parser.add_argument('-re',  dest='reread', action='store_true')
    parser.add_argument('-mod', dest='mod',    default=None)
    parser.add_argument('-med', dest='med',    action='store_true')
    parser.add_argument('-prev',dest='prev',   action='store_true')
    parser.add_argument('-h',   dest='help',   action='store_true')
    return parser

def get_chunk_size(args) -> int:
    if args.mod and args.mod in MOD_SIZES: return MOD_SIZES[args.mod]
    if args.med: return MED_SIZE
    return MED_SIZE  # default

def make_state_enc(method: str, shift=3, key='KEY') -> StreamState:
    m = method.lower()
    if m == 'caesar':       return StreamState('caesar', shift=shift)
    if m in ('vigenere','vig'): return StreamState('vigenere', key=key)
    if m == 'rot13':        return StreamState('rot13')
    if m == 'atbash':       return StreamState('atbash')
    if m in ('base64','b64'): return StreamState('base64')
    if m == 'hex':          return StreamState('hex')
    if m in ('binary','bin'): return StreamState('binary')
    if m == 'morse':        return StreamState('morse')
    if m == 'leet':         return StreamState('leet1')
    if m == 'leet2':        return StreamState('leet2')
    if m == 'xor':          return StreamState('xor', key=key)
    if m in ('homoglyph','uni'): return StreamState('homoglyph')
    if m in ('rev','reverse'):   return StreamState('rev_lines')
    if m == 'zalgo':        return StreamState('homoglyph')  # zalgo via full-load
    return None

def make_state_dec(method: str, shift=3, key='KEY') -> StreamState:
    m = method.lower()
    if m == 'caesar':       return StreamState('caesar_dec', shift=shift)
    if m in ('vigenere','vig'): return StreamState('vigenere_dec', key=key)
    if m == 'rot13':        return StreamState('rot13')
    if m == 'atbash':       return StreamState('atbash')
    if m in ('base64','b64'): return StreamState('base64_dec')
    if m == 'hex':          return StreamState('hex_dec')
    if m in ('binary','bin'): return StreamState('binary_dec')
    if m == 'morse':        return StreamState('morse_dec')
    if m in ('leet','unleet'): return StreamState('unleet')
    if m == 'xor':          return StreamState('xor_dec', key=key)
    if m in ('rev','reverse'):  return StreamState('rev_lines')
    return None

def auto_output(input_path: str, suffix='_chx') -> str:
    p = Path(input_path)
    return str(p.parent / (p.stem + suffix + p.suffix))

def run_cli(args):
    """Jalankan dari argumen CLI."""
    if args.help or (not args.file and not args.cipher and not args.decode and not args.reread):
        print(HELP_TEXT); return

    if not args.file:
        err("Wajib gunakan -f untuk input file"); return

    if not os.path.exists(args.file):
        err(f"File tidak ditemukan: {args.file}"); return

    fsize = os.path.getsize(args.file)
    enc   = detect_enc(args.file)
    out   = args.output or auto_output(args.file)
    chunk = get_chunk_size(args)

    print(BANNER)
    info(f"Input  : {args.file}  ({fmt_size(fsize)})")
    info(f"Enc    : {enc}")
    info(f"Chunk  : {fmt_size(chunk)}")

    # Preview
    if args.prev:
        print(clr("\n  ── Preview ──", C.YELLOW))
        with open(args.file,'r',encoding=enc,errors='replace') as f:
            for i,line in enumerate(f):
                if i >= 10: break
                print(f"  {clr(str(i+1).rjust(3),C.DIM)}│ {line}", end='')
        print()

    # -re: binary reader
    if args.reread:
        read_binary(args.file, out)
        return

    # -c: encrypt/obfuscate
    if args.cipher:
        if args.cipher.lower() == 'obfuscate':
            interactive_obfuscate_file(args.file, out, enc, chunk)
            return
        state = make_state_enc(args.cipher, args.shift, args.key)
        if not state:
            err(f"Metode tidak dikenal: {args.cipher}"); return
        process_file(args.file, out, state, chunk, enc)
        return

    # -de: decrypt/deobfuscate
    if args.decode:
        if args.decode.lower() == 'auto':
            with open(args.file,'r',encoding=enc,errors='replace') as f:
                content = f.read(10*1024*1024)  # max 10 MB untuk auto-detect
            auto_detect(content)
            return
        state = make_state_dec(args.decode, args.shift, args.key)
        if not state:
            err(f"Metode tidak dikenal: {args.decode}"); return
        process_file(args.file, out, state, chunk, enc)
        return

    err("Gunakan -c (enkripsi) atau -de (dekripsi) atau -re (baca binary)")

def interactive_obfuscate_file(inp, out, enc, chunk):
    print(clr("\n  Pilih metode obfuskasi:", C.ORANGE))
    opts = [("1","Leet L1"),("2","Leet L2"),("3","XOR+Hex"),("4","Reverse baris"),
            ("5","Homoglyph"),("6","Zalgo")]
    for n,name in opts: print(f"  {clr(f'[{n}]',C.YELLOW)} {name}")
    c = input(clr("  Pilihan > ", C.CYAN)).strip()
    state = None
    if c=='1': state = StreamState('leet1')
    elif c=='2': state = StreamState('leet2')
    elif c=='3':
        k = input(clr("  XOR Key > ", C.CYAN)).strip() or "X"
        state = StreamState('xor', key=k)
        warn(f"Simpan key '{k}' untuk decode!")
    elif c=='4': state = StreamState('rev_lines')
    elif c=='5': state = StreamState('homoglyph')
    elif c=='6':
        # Zalgo perlu full load
        with open(inp,'r',encoding=enc,errors='replace') as f: content = f.read()
        with open(out,'w',encoding=enc,errors='replace') as f: f.write(zalgo(content,1))
        ok(f"Tersimpan: {out}"); return
    if state: process_file(inp, out, state, chunk, enc)

# ══════════════════════════════════════════════════════════════════
#  INTERACTIVE EASY MODE
# ══════════════════════════════════════════════════════════════════

def interactive():
    while True:
        banner()
        print(f"\n  {clr('[A]', C.CYAN+C.BOLD)}  Mode Teks — Input Manual")
        print(f"  {clr('[B]', C.GREEN+C.BOLD)}  Mode File — Enkripsi/Obfuskasi file")
        print(f"  {clr('[C]', C.MAGENTA+C.BOLD)}  Mode File — Dekripsi/De-Obfuskasi file")
        print(f"  {clr('[D]', C.YELLOW+C.BOLD)}  Auto-Detect (paste ciphertext)")
        print(f"  {clr('[E]', C.ORANGE+C.BOLD)}  📂 Binary Reader — baca file tidak terbaca")
        print(f"  {clr('[H]', C.DIM)}  Help & daftar flag CLI")
        print(f"  {clr('[Q]', C.DIM)}  Keluar\n")
        print(clr("  TIP: bisa juga jalankan langsung:", C.DIM))
        print(clr("  chx.py -f file.txt -c caesar -s 3 -o out.txt\n", C.DIM))

        ch = input(clr("  Pilihan > ", C.CYAN)).strip().upper()
        if ch == 'Q': print(clr("\n  // CHX SESSION ENDED //\n", C.DIM)); break
        elif ch == 'H': print(HELP_TEXT); input(clr("  Enter...", C.DIM)); continue
        elif ch == 'A': mode_text()
        elif ch == 'B': mode_file_enc()
        elif ch == 'C': mode_file_dec()
        elif ch == 'D':
            print(clr("\n  Paste ciphertext (Enter 2x selesai):", C.DIM))
            lines, prev = [], False
            while True:
                try: line = input()
                except EOFError: break
                if line == '' and prev: break
                prev = (line == '')
                lines.append(line)
            while lines and lines[-1] == '': lines.pop()
            auto_detect('\n'.join(lines))
            input(clr("  Enter...", C.DIM)); continue
        elif ch == 'E':
            path = input(clr("\n  Path file binary > ", C.MAGENTA)).strip().strip('"')
            if not os.path.exists(path): err("File tidak ditemukan")
            else:
                out = input(clr(f"  Output (Enter = {auto_output(path,'_chxread')}) > ", C.DIM)).strip()
                out = out or auto_output(path,'_chxread')
                read_binary(path, out)
            input(clr("  Enter...", C.DIM)); continue
        else: print(clr("  [!] Tidak valid.", C.RED))

        print(); input(clr("  Enter untuk kembali...", C.DIM))

# ── Mode A: Teks manual ──────────────────────────────────────────
ENC_METHODS  = [
    ("1","Caesar","shift"),("2","Vigenère","key"),("3","ROT13","-"),
    ("4","Atbash","-"),("5","Base64","-"),("6","Hex","-"),("7","Binary","-"),
    ("8","Morse","-"),("9","Leet L1","-"),("10","Leet L2","-"),
    ("11","XOR+Hex","key"),("12","Reverse baris","-"),("13","Homoglyph","-"),("14","Zalgo","-"),
]

def get_multiline(prompt):
    print(clr(f"\n  {prompt} (Enter 2x = selesai, bisa multiline/paste):", C.DIM))
    lines, prev = [], False
    while True:
        try: line = input()
        except EOFError: break
        if line == '' and prev: break
        prev = (line == '')
        lines.append(line)
    while lines and lines[-1] == '': lines.pop()
    return '\n'.join(lines)

def show_result(result, method, mode):
    colors = {"ENC":C.CYAN,"DEC":C.GREEN,"OBF":C.ORANGE,"DE-OBF":C.YELLOW}
    labels = {"ENC":"ENKRIPSI","DEC":"DEKRIPSI","OBF":"OBFUSKASI","DE-OBF":"DE-OBF"}
    col = colors.get(mode, C.RESET)
    print(clr(f"\n  ┌─────────────────────────────────────────────────────┐", col))
    print(clr(f"  │  ✔ [{labels.get(mode,mode)}] {method}", col))
    print(clr(f"  └─────────────────────────────────────────────────────┘", col))
    for line in result.split('\n')[:60]:
        print(f"  {clr(line, col)}")
    if result.count('\n') > 60:
        print(clr(f"  ... ({result.count(chr(10))-60} baris tersembunyi)", C.DIM))
    print()

def mode_text():
    text = get_multiline("Input teks")
    if not text: err("Teks kosong!"); return
    print(clr("\n  ── ENKRIPSI ──", C.CYAN))
    for n,name,extra in ENC_METHODS:
        tag = clr(f"[{n}]",C.YELLOW)
        print(f"  {tag:<6} {clr(name,C.RESET):<18} {clr(f'— {extra}',C.DIM)}")
    print(clr("\n  ── DEKRIPSI ──", C.GREEN))
    print(f"  {clr('[d0]',C.GREEN)} AUTO-DETECT")
    for n,name,_ in ENC_METHODS:
        print(f"  {clr(f'd{n}',C.GREEN):<6} De-{name}")

    ch = input(clr("\n  Pilihan > ", C.CYAN)).strip().lower()
    decrypt = ch.startswith('d')
    c = ch.lstrip('d')

    if c == '0': auto_detect(text); return

    mapping = {
        '1':('caesar','ENC' if not decrypt else 'DEC'),
        '2':('vigenere','ENC' if not decrypt else 'DEC'),
        '3':('rot13','ENC'),
        '4':('atbash','ENC'),
        '5':('base64','ENC' if not decrypt else 'DEC'),
        '6':('hex','ENC' if not decrypt else 'DEC'),
        '7':('binary','ENC' if not decrypt else 'DEC'),
        '8':('morse','ENC' if not decrypt else 'DEC'),
        '9':('leet1','OBF' if not decrypt else 'DE-OBF'),
        '10':('leet2','OBF' if not decrypt else 'DE-OBF'),
        '11':('xor','OBF' if not decrypt else 'DE-OBF'),
        '12':('rev','OBF' if not decrypt else 'DE-OBF'),
        '13':('homoglyph','OBF'),
        '14':('zalgo','OBF'),
    }
    if c not in mapping: err("Tidak valid"); return
    method, mode = mapping[c]

    shift, key = 3, 'KEY'
    if method == 'caesar':
        s = input(clr("  Shift (1-25) > ", C.CYAN)).strip()
        shift = int(s) if s.isdigit() else 3
    elif method in ('vigenere','xor'):
        key = input(clr("  Key > ", C.CYAN)).strip() or 'KEY'

    enc_fns = {
        'caesar':    lambda t: caesar(t, shift),
        'vigenere':  lambda t: vigenere(t, key),
        'rot13':     lambda t: rot13(t),
        'atbash':    lambda t: atbash(t),
        'base64':    lambda t: to_b64(t),
        'hex':       lambda t: to_hex(t),
        'binary':    lambda t: to_bin(t),
        'morse':     lambda t: to_morse(t),
        'leet1':     lambda t: leet(t,1),
        'leet2':     lambda t: leet(t,2),
        'xor':       lambda t: xor_enc(t, key),
        'rev':       lambda t: rev_lines(t),
        'homoglyph': lambda t: homoglyph(t),
        'zalgo':     lambda t: zalgo(t,2),
    }
    dec_fns = {
        'caesar':    lambda t: caesar(t, shift, True),
        'vigenere':  lambda t: vigenere(t, key, True),
        'rot13':     lambda t: rot13(t),
        'atbash':    lambda t: atbash(t),
        'base64':    lambda t: from_b64(t),
        'hex':       lambda t: from_hex(t),
        'binary':    lambda t: from_bin(t),
        'morse':     lambda t: from_morse(t),
        'leet1':     lambda t: unleet(t),
        'leet2':     lambda t: unleet(t),
        'xor':       lambda t: xor_dec(t, key),
        'rev':       lambda t: rev_lines(t),
        'homoglyph': lambda t: t,
        'zalgo':     lambda t: t,
    }
    fns = dec_fns if decrypt else enc_fns
    result = fns[method](text)
    show_result(result, f"{method.upper()} {'dec' if decrypt else 'enc'}", mode)

# ── Mode B/C: File ───────────────────────────────────────────────
def pick_file():
    path = input(clr("\n  Path file > ", C.MAGENTA)).strip().strip('"').strip("'")
    if not os.path.exists(path): err(f"File tidak ditemukan: {path}"); return None, None
    enc = detect_enc(path)
    sz  = os.path.getsize(path)
    info(f"Ukuran: {fmt_size(sz)}  |  Encoding: {enc}")
    return path, enc

def pick_output(inp):
    default = auto_output(inp)
    o = input(clr(f"  Output (Enter = {default}) > ", C.DIM)).strip()
    return o or default

def pick_chunk():
    print(clr("\n  Chunk size:", C.DIM))
    print(f"  {clr('[1]',C.DIM)} 4 MB  (default, streaming)  {clr('[2]',C.DIM)} 100 MB"
          f"  {clr('[3]',C.DIM)} 200 MB  {clr('[4]',C.DIM)} 300 MB  {clr('[5]',C.DIM)} 500 MB")
    c = input(clr("  > ", C.DIM)).strip()
    return {
        '1': MED_SIZE, '2': MOD_SIZES['1'], '3': MOD_SIZES['2'],
        '4': MOD_SIZES['3'], '5': MOD_SIZES['5']
    }.get(c, MED_SIZE)

def mode_file_enc():
    path, enc = pick_file()
    if not path: return

    print(clr("\n  Metode enkripsi/obfuskasi:", C.CYAN))
    for n,name,extra in ENC_METHODS:
        print(f"  {clr(f'[{n}]',C.YELLOW):<6} {clr(name,C.RESET):<18} {clr(f'— {extra}',C.DIM)}")

    ch = input(clr("\n  Pilihan > ", C.CYAN)).strip()
    state = make_state_enc({'1':'caesar','2':'vigenere','3':'rot13','4':'atbash',
                             '5':'base64','6':'hex','7':'binary','8':'morse',
                             '9':'leet','10':'leet2','11':'xor','12':'rev',
                             '13':'homoglyph','14':'zalgo'}.get(ch,''), 3, 'KEY')

    shift, key = 3, 'KEY'
    if ch == '1':
        s = input(clr("  Shift > ", C.CYAN)).strip()
        shift = int(s) if s.isdigit() else 3
        state = make_state_enc('caesar', shift)
    elif ch in ('2','11'):
        key = input(clr("  Key > ", C.CYAN)).strip() or 'KEY'
        if ch == '11': warn(f"Simpan key '{key}' untuk decode nanti!")
        state = make_state_enc('vigenere' if ch=='2' else 'xor', key=key)
    elif ch == '14':  # zalgo full-load
        out = pick_output(path)
        with open(path,'r',encoding=enc,errors='replace') as f: content = f.read()
        with open(out,'w',encoding=enc,errors='replace') as f: f.write(zalgo(content,1))
        ok(f"Tersimpan: {out}"); return

    if not state: err("Metode tidak valid"); return
    out = pick_output(path)
    chunk = pick_chunk()
    if os.path.exists(out):
        if input(clr(f"  File output ada! Timpa? [y/N] > ", C.YELLOW)).strip().lower() != 'y': return
    process_file(path, out, state, chunk, enc)

def mode_file_dec():
    path, enc = pick_file()
    if not path: return

    print(clr("\n  Metode dekripsi/de-obfuskasi:", C.GREEN))
    print(f"  {clr('[0]',C.GREEN)} AUTO-DETECT (rekomendasi jika lupa metode)")
    for n,name,extra in ENC_METHODS:
        print(f"  {clr(f'[{n}]',C.YELLOW):<6} De-{clr(name,C.RESET)}")

    ch = input(clr("\n  Pilihan > ", C.CYAN)).strip()

    if ch == '0':
        sz = os.path.getsize(path)
        sample = min(sz, 10*1024*1024)
        with open(path,'r',encoding=enc,errors='replace') as f: content = f.read(sample)
        if sz > sample: warn(f"File besar — auto-detect hanya pada {fmt_size(sample)} pertama")
        auto_detect(content); return

    shift, key = 3, 'KEY'
    if ch == '1':
        s = input(clr("  Shift > ", C.CYAN)).strip()
        shift = int(s) if s.isdigit() else 3
    elif ch in ('2','11'):
        key = input(clr("  Key > ", C.CYAN)).strip() or 'KEY'

    state = make_state_dec({'1':'caesar','2':'vigenere','3':'rot13','4':'atbash',
                             '5':'base64','6':'hex','7':'binary','8':'morse',
                             '9':'leet','10':'leet2','11':'xor','12':'rev',
                             '13':'homoglyph','14':'zalgo'}.get(ch,''), shift, key)
    if not state: err("Metode tidak valid"); return
    out = pick_output(path)
    chunk = pick_chunk()
    if os.path.exists(out):
        if input(clr(f"  File output ada! Timpa? [y/N] > ", C.YELLOW)).strip().lower() != 'y': return
    process_file(path, out, state, chunk, enc)

# ══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) <= 1:
        interactive()
    else:
        parser = build_parser()
        args, _ = parser.parse_known_args()
        run_cli(args)

if __name__ == '__main__':
    main()
