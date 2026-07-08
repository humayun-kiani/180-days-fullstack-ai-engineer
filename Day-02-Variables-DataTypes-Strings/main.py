# MAD LIBS GENERATOR
# Day 02 - 180 Days Full Stack AI Engineer Roadmap


import random

def get_word_input(prompt):
    """Get a word from the user and clean it up."""
    word = input(prompt).strip()       # .strip() removes accidental spaces
    return word.lower()                # .lower() makes it lowercase


def story_one(name, adjective, noun, verb, place, animal, food):
    """Story template 1: The Unexpected Adventure"""
    story = f"""

    THE UNEXPECTED ADVENTURE

    One {adjective} morning, {name.title()} woke up to find a {animal}
    sitting on their {noun}. The {animal} was eating {food} and
    looked very confused.

    {name.title()} decided to {verb} as fast as possible toward the
    nearest {place}. Along the way, they met a {adjective} wizard
    who offered them more {food} in exchange for the {noun}.

    In the end, {name.title()} and the {animal} became best friends
    and opened a {food} shop in {place}. It was the most {adjective}
    shop in the entire world.

    THE END.
    """
    return story


def story_two(name, adjective, noun, verb, place, animal, food):
    """Story template 2: The Tech Startup"""
    story = f"""
    THE TECH STARTUP
    {name.title()} had a {adjective} idea: build an app where people
    could {verb} with their {animal} online. Everyone said it was a
    {adjective} plan that would never work.

    But {name.title()} kept coding in their {place}, surviving only
    on {food} and coffee. They used a {noun} as their main computer
    (don't ask how).

    Six months later, the app had 1 million {animal} users and was
    valued at a {adjective} amount of money. The secret? They added
    a feature to {verb} while eating {food}.

    THE END.
    """
    return story


def collect_words():
    """Collect all the words needed for the story from the user."""
    print("\n" + "=" * 50)
    print("  Answer these questions (don't think too hard!)")

    name = get_word_input("\nEnter a person's name: ")
    adjective = get_word_input("Enter an adjective: ")
    noun = get_word_input("Enter a noun: ")
    verb = get_word_input("Enter a verb: ")
    place = get_word_input("Enter a place: ")
    animal = get_word_input("Enter an animal: ")
    food = get_word_input("Enter a food: ")

    return name, adjective, noun, verb, place, animal, food


def display_word_summary(name, adjective, noun, verb, place, animal, food):
    """Show the user what words they entered."""
    print("\n--- Your words ---")
    print(f"  Name:      {name.title()}")
    print(f"  Adjective: {adjective}")
    print(f"  Noun:      {noun}")
    print(f"  Verb:      {verb}")
    print(f"  Place:     {place}")
    print(f"  Animal:    {animal}")
    print(f"  Food:      {food}")


def play_game():
    """Main game function."""

    # Welcome banner
    print("\n" + "=" * 50)
    print("       WELCOME TO THE MAD LIBS GENERATOR")
    print("  Fill in the words. Prepare to laugh at the story.")

    # List of story functions to randomly pick from
    stories = [story_one, story_two]

    while True:
        # Collect words from the user
        words = collect_words()
        name, adjective, noun, verb, place, animal, food = words

        # Show word summary
        display_word_summary(name, adjective, noun, verb, place, animal, food)

        # Pick a random story
        chosen_story = random.choice(stories)

        # Generate and display the story
        print("\nHere is your Mad Libs story!\n")
        result = chosen_story(name, adjective, noun, verb, place, animal, food)
        print(result)

        # Word statistics (using string methods!)
        total_chars = len(name) + len(adjective) + len(noun) + len(verb) + len(place) + len(animal) + len(food)
        print(f"Fun fact: Your words contained {total_chars} total characters!")
        print(f"The longest word you entered was: '{max([name, adjective, noun, verb, place, animal, food], key=len)}'")

        # Play again?
        print("\n" + "-" * 50)
        play_again = input("Play again with different words? (yes/no): ").strip().lower()

        if play_again not in ["yes", "y"]:
            print("\n Thanks for playing Mad Libs!")
            print(" Keep learning, keep building. See you on Day 3!")
            print("=" * 50 + "\n")
            break


# Entry point
if __name__ == "__main__":
    play_game()