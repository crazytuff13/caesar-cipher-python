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
    encrypted_text = text.translate(translation_table)
    return encrypted_text


def encrypt(text, shift):
    return caesar(text, shift)


def decrypt(text, shift):
    return caesar(text, shift, encrypt=False)


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
            result = encrypt(message, shift)
            print(f"Encrypted: {result}\n")
        elif mode == 'd':
            result = decrypt(message, shift)
            print(f"Decrypted: {result}\n")
        else:
            print("Invalid option. Type 'e' or 'd'.\n")