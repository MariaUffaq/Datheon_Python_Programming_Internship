import random

MAX_MISTAKES = 6

STAGES = [
    """
     +---+
     |   |
         |
         |
         |
         |
    =========""",
    """
     +---+
     |   |
     O   |
         |
         |
         |
    =========""",
    """
     +---+
     |   |
     O   |
     |   |
         |
         |
    =========""",
    """
     +---+
     |   |
     O   |
    /|   |
         |
         |
    =========""",
    """
     +---+
     |   |
     O   |
    /|\\  |
         |
         |
    =========""",
    """
     +---+
     |   |
     O   |
    /|\\  |
    /    |
         |
    =========""",
    """
     +---+
     |   |
     O   |
    /|\\  |
    / \\  |
         |
    =========""",
]


def load_words(path="words.txt"):
    """Load words from the downloaded file; fall back to a built-in list."""
    try:
        with open(path) as f:
            words = [w.strip().lower() for w in f if w.strip().isalpha() and len(w.strip()) > 3]
        if words:
            return words
    except FileNotFoundError:
        pass
    return ["python", "hangman", "keyboard", "program", "variable", "function"]


def masked_word(word, guessed):
    return " ".join(ch if ch in guessed else "_" for ch in word)


def get_guess(guessed):
    while True:
        guess = input("Guess a letter: ").strip().lower()
        if len(guess) != 1 or not guess.isalpha():
            print("Please enter a single letter.")
        elif guess in guessed:
            print("You already guessed that letter. No penalty, try another.")
        else:
            return guess


def play():
    word = random.choice(load_words())
    guessed = set()
    mistakes = 0

    print("=== HANGMAN ===")
    while mistakes < MAX_MISTAKES:
        print(STAGES[mistakes])
        print("\nWord:", masked_word(word, guessed))
        print("Guessed:", " ".join(sorted(guessed)) or "-")
        print(f"Attempts left: {MAX_MISTAKES - mistakes}\n")

        guess = get_guess(guessed)
        guessed.add(guess)

        if guess in word:
            print("Correct!")
            if all(ch in guessed for ch in word):
                print(f"\n🎉 You won! The word was '{word}'.")
                return
        else:
            mistakes += 1
            print("Wrong!")

    print(STAGES[MAX_MISTAKES])
    print(f"\n💀 You lost. The word was '{word}'.")


def main():
    while True:
        play()
        if input("\nPlay again? (y/n): ").strip().lower() != "y":
            print("Thanks for playing!")
            break


if __name__ == "__main__":
    main()