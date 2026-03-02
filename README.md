# CHX
Encryption, Decryption, Obfuscate, File Reader

File types based on magic bytes (PE, ELF, LNK, ZIP, etc.)
Entropy analysis — detect if a file is encrypted/compressed
Hex dump of the first 256 bytes
ASCII string & UTF-16 string (Windows format)
JWT auto-decode → like your example: directly output username: john_doe, role: user, exp: ...
URL, Windows path, Linux path, email, registry key, GUID, version
Base64 embedded in binary

## TL;DR

```
# Encrypt file HTML/txt
python3 chx.py -f file.html -c caesar -s 7 -o enc.html

# Decrypt
python3 chx.py -f enc.html -de caesar -s 7 -o dec.html

# Vigenère
python3 chx.py -f data.txt -c vigenere -k FARIDA -o out.txt

# Obfuscate
python3 chx.py -f code.html -c leet -o obf.html

# XOR
python3 chx.py -f secret.txt -c xor -k MYKEY -o enc.txt

# For file above default. 100GB
python3 chx.py -f huge.log -c rot13 -mod 3 -o out.log

# Read binary / file cant be reading
python3 chx.py -f app.bin -re -o analisis.txt

# Auto-detect if someone forgot the key (need alot maintaining)
python3 chx.py -f cipher.txt -de auto

# Help
python3 chx.py -h
```
