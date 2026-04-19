def caesar(text, shift, encrypt=True):
    if not isinstance(shift, int):
        return 'Shift must be an integer value.'
    if shift < 1 or shift > 25:
        return 'Shift must be an integer between 1 and 25.'

    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    if not encrypt:
        shift = -shift

    shifted_alphabet = alphabet[shift:] + alphabet[:shift]
    translation_table = str.maketrans(alphabet + alphabet.upper(), shifted_alphabet + shifted_alphabet.upper())
    return text.translate(translation_table)


def encrypt(text, shift):
    return caesar(text, shift)


def decrypt(text, shift):
    return caesar(text, shift, encrypt=False)


def rot13(text):
    return caesar(text, 13)


def vigenere(text, keyword, encrypt=True):
    if not keyword.isalpha():
        return 'Keyword must contain letters only.'

    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    keyword = keyword.lower()
    result = []
    key_index = 0

    for char in text:
        if char.isalpha():
            shift = alphabet.index(keyword[key_index % len(keyword)])
            if not encrypt:
                shift = -shift
            base = ord('A') if char.isupper() else ord('a')
            shifted = chr((ord(char) - base + shift) % 26 + base)
            result.append(shifted)
            key_index += 1
        else:
            result.append(char)

    return ''.join(result)


if __name__ == "__main__":
    print("=== Caesar Cipher Chat ===")
    print("Type 'quit' to exit.\n")

    while True:
        message = input("Enter a message: ")
        if message.lower() == 'quit':
            print("Goodbye!")
            break

        mode = input("Encrypt or decrypt? (e/d): ").lower()
        shift = input("Enter shift (1-25): ")

        if not shift.isdigit():
            print("Invalid shift. Try again.\n")
            continue

        shift = int(shift)

        if mode == 'e':
            print(f"Encrypted: {encrypt(message, shift)}\n")
        elif mode == 'd':
            print(f"Decrypted: {decrypt(message, shift)}\n")
        else:
            print("Invalid option. Type 'e' or 'd'.\n")