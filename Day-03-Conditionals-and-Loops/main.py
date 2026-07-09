# ============================================================
# NUMBER GUESSING GAME
# Day 03 - 180 Days Full Stack AI Engineer Roadmap
# ============================================================

import random


# Global variable to track best score across all games
best_score = None


def get_performance_rating(attempts):
    """Return a performance rating based on number of attempts."""
    if attempts == 1:
        return "IMPOSSIBLE! Are you psychic?"
    elif attempts <= 3:
        return "Outstanding!"
    elif attempts <= 5:
        return "Great job!"
    elif attempts <= 7:
        return "You got it!"
    else:
        return "Better luck next time!"


def display_hint(guess, secret_number):
    """Display a hint based on how close the guess is."""
    difference = abs(guess - secret_number)

    if difference == 0:
        return "CORRECT!"
    elif difference <= 5:
        hint = "Too high! Very close!" if guess > secret_number else "Too low! Very close!"
    elif difference <= 15:
        hint = "Too high! Getting warmer..." if guess > secret_number else "Too low! Getting warmer..."
    elif difference <= 30:
        hint = "Too high! Lukewarm..." if guess > secret_number else "Too low! Lukewarm..."
    else:
        hint = "Too high! Ice cold!" if guess > secret_number else "Too low! Ice cold!"

    return hint


def get_valid_guess(attempt, max_attempts):
    """Get a valid number guess from the user."""
    while True:
        try:
            guess_input = input(
                f"\nAttempt {attempt}/{max_attempts} — Enter your guess (1-100): "
            )
            guess = int(guess_input)

            if guess < 1 or guess > 100:
                print("Please enter a number between 1 and 100.")
                continue

            return guess

        except ValueError:
            print("That is not a valid number. Please try again.")


def play_round():
    """Play one round of the guessing game. Returns number of attempts or None if gave up."""
    global best_score

    # Generate secret number
    secret_number = random.randint(1, 100)
    max_attempts = 7
    attempts_used = 0
    guesses_history = []

    print("\n" + "=" * 50)
    print("  NEW GAME STARTED")
    print(f"  I am thinking of a number between 1 and 100.")
    print(f"  You have {max_attempts} attempts. Good luck!")
    print("=" * 50)

    # Main guessing loop
    while attempts_used < max_attempts:
        attempts_used += 1
        remaining = max_attempts - attempts_used

        # Get valid guess from user
        guess = get_valid_guess(attempts_used, max_attempts)
        guesses_history.append(guess)

        # Check the guess
        hint = display_hint(guess, secret_number)

        if guess == secret_number:
            # Correct guess
            print(f"\n {hint}")
            print(f"   The number was {secret_number}!")
            print(f"   You got it in {attempts_used} attempt(s)!")

            # Update best score
            if best_score is None or attempts_used < best_score:
                best_score = attempts_used
                print(f"New best score: {best_score} attempt(s)!")
            else:
                print(f"Your best score is still: {best_score} attempt(s)")

            # Show performance rating
            rating = get_performance_rating(attempts_used)
            print(f"Rating: {rating}")

            # Show guess history
            print(f"\nYour guesses were: {guesses_history}")

            return attempts_used

        else:
            # Wrong guess
            print(f" {hint}")
            if remaining > 0:
                print(f"   {remaining} attempt(s) remaining.")

    # Ran out of attempts
    print(f"\n Game Over! You ran out of attempts.")
    print(f"   The number was: {secret_number}")
    print(f"   Your guesses were: {guesses_history}")

    return None


def show_statistics(games_played, games_won, total_attempts):
    """Display game statistics."""
    print("\n" + "=" * 50)
    print("  YOUR STATISTICS")
    print("=" * 50)
    print(f"  Games played:  {games_played}")
    print(f"  Games won:     {games_won}")
    print(f"  Games lost:    {games_played - games_won}")

    if games_played > 0:
        win_rate = (games_won / games_played) * 100
        print(f"  Win rate:      {win_rate:.1f}%")

    if games_won > 0:
        avg_attempts = total_attempts / games_won
        print(f"  Avg attempts:  {avg_attempts:.1f} per win")

    if best_score is not None:
        print(f"  Best score:    {best_score} attempt(s)")

    print("=" * 50)


def main():
    """Main function to run the game."""
    games_played = 0
    games_won = 0
    total_attempts = 0

    # Welcome screen
    print("\n" + "=" * 50)
    print("    WELCOME TO THE NUMBER GUESSING GAME")
    print("=" * 50)
    print("  Rules:")
    print("  - I pick a number between 1 and 100")
    print("  - You have 7 attempts to guess it")
    print("  - I will tell you if you are too high or too low")
    print("  - Closer guesses get warmer hints!")
    print("=" * 50)

    # Game loop
    while True:
        result = play_round()
        games_played += 1

        if result is not None:
            games_won += 1
            total_attempts += result

        # Ask to play again
        print("\n" + "-" * 50)
        play_again = input("Play again? (yes/no): ").strip().lower()

        if play_again in ["yes", "y"]:
            continue
        else:
            # Show final statistics before quitting
            show_statistics(games_played, games_won, total_attempts)
            print("\n  Thanks for playing! See you on Day 4!")
            print("  Keep building, keep learning.")
            print("=" * 50 + "\n")
            break


# Entry point
if __name__ == "__main__":
    main()