from datetime import date
import random

# A collection of motivational quotes
quotes = [
    "The secret of getting ahead is getting started. — Mark Twain",
    "It always seems impossible until it's done. — Nelson Mandela",
    "Code is like humor. When you have to explain it, it's bad. — Cory House",
    "First, solve the problem. Then, write the code. — John Johnson",
    "Every expert was once a beginner. — Helen Hayes",
    "The best time to start was yesterday. The next best time is now.",
    "Learning to code is learning to create and innovate.",
]


def show_welcome():
    """Display a personalized welcome message with today's date and a quote."""
    
    # Get and format today's date
    today = date.today()
    formatted_date = today.strftime("%B %d, %Y")
    
    # Pick a random motivational quote
    quote = random.choice(quotes)
    
    # Display the welcome banner
    print("   PERSONAL INTRODUCTION APP")

    
    # Get user input
    name = input("\nWhat is your name? ")
    
    # Display personalized output
    print(f"\nHello, {name}!")
    print(f"Today is: {formatted_date}")
    print("\nYour motivational quote for today:")
    print(f'   "{quote}"')
    print("\nKeep building, keep learning!")



if __name__ == "__main__":
    show_welcome()